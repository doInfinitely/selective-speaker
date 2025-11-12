package ai.gauntlet.selectivespeaker.service

import android.app.Notification
import android.app.PendingIntent
import android.app.Service
import android.content.Intent
import android.location.Location
import android.media.AudioFormat
import android.media.AudioRecord
import android.media.MediaRecorder
import android.os.Build
import android.os.IBinder
import androidx.core.app.NotificationCompat
import ai.gauntlet.selectivespeaker.R
import ai.gauntlet.selectivespeaker.SelectiveSpeakerApp
import ai.gauntlet.selectivespeaker.api.ApiClient
import ai.gauntlet.selectivespeaker.api.ChunkSubmitRequest
import ai.gauntlet.selectivespeaker.ui.MainActivity
import ai.gauntlet.selectivespeaker.util.AudioUtils
import ai.gauntlet.selectivespeaker.util.LocationHelper
import kotlinx.coroutines.*
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.asRequestBody
import okhttp3.RequestBody.Companion.toRequestBody
import java.io.File
import android.util.Log

class RecordingService : Service() {
    
    companion object {
        private const val TAG = "RecordingService"
        private const val NOTIFICATION_ID = 1
        private const val SAMPLE_RATE = 16000
        private const val CHANNEL_CONFIG = AudioFormat.CHANNEL_IN_MONO
        private const val AUDIO_FORMAT = AudioFormat.ENCODING_PCM_16BIT
        private const val CHUNK_DURATION_SEC = 30 // Record in 30 second chunks
        private const val VAD_THRESHOLD = 100f // Voice activity detection threshold (lowered for normal speech)
    }
    
    private var audioRecord: AudioRecord? = null
    private val serviceScope = CoroutineScope(Dispatchers.IO + SupervisorJob())
    private var isRecording = false
    private val locationHelper by lazy { LocationHelper(this) }
    
    override fun onCreate() {
        super.onCreate()
        Log.d(TAG, "Recording service created")
    }
    
    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        Log.d(TAG, "Starting recording service")
        startForeground(NOTIFICATION_ID, createNotification())
        startRecording()
        return START_STICKY
    }
    
    override fun onBind(intent: Intent?): IBinder? = null
    
    override fun onDestroy() {
        Log.d(TAG, "Stopping recording service")
        stopRecording()
        serviceScope.cancel()
        super.onDestroy()
    }
    
    private fun createNotification(): Notification {
        val notificationIntent = Intent(this, MainActivity::class.java)
        val pendingIntent = PendingIntent.getActivity(
            this, 0, notificationIntent,
            PendingIntent.FLAG_IMMUTABLE
        )
        
        return NotificationCompat.Builder(this, SelectiveSpeakerApp.NOTIFICATION_CHANNEL_ID)
            .setContentTitle("Selective Speaker Recording")
            .setContentText("Continuously recording your voice")
            .setSmallIcon(R.drawable.ic_notification)
            .setContentIntent(pendingIntent)
            .setOngoing(true)
            .build()
    }
    
    private fun startRecording() {
        if (isRecording) return
        
        val bufferSize = AudioRecord.getMinBufferSize(
            SAMPLE_RATE,
            CHANNEL_CONFIG,
            AUDIO_FORMAT
        )
        
        Log.d(TAG, "Initializing AudioRecord with buffer size: $bufferSize")
        
        try {
            audioRecord = AudioRecord(
                MediaRecorder.AudioSource.VOICE_RECOGNITION,
                SAMPLE_RATE,
                CHANNEL_CONFIG,
                AUDIO_FORMAT,
                bufferSize
            )
            
            if (audioRecord?.state != AudioRecord.STATE_INITIALIZED) {
                Log.e(TAG, "AudioRecord failed to initialize!")
                audioRecord?.release()
                audioRecord = null
                return
            }
            
            Log.d(TAG, "AudioRecord initialized successfully, starting recording...")
            isRecording = true
            audioRecord?.startRecording()
            
            serviceScope.launch {
                recordAudioChunks()
            }
        } catch (e: SecurityException) {
            Log.e(TAG, "Permission denied for audio recording", e)
        } catch (e: Exception) {
            Log.e(TAG, "Error starting AudioRecord", e)
        }
    }
    
    private fun stopRecording() {
        isRecording = false
        audioRecord?.stop()
        audioRecord?.release()
        audioRecord = null
    }
    
    private suspend fun recordAudioChunks() {
        val bufferSize = AudioRecord.getMinBufferSize(
            SAMPLE_RATE,
            CHANNEL_CONFIG,
            AUDIO_FORMAT
        )
        
        val buffer = ShortArray(bufferSize)
        val chunkSamples = SAMPLE_RATE * CHUNK_DURATION_SEC
        val chunkBuffer = mutableListOf<Short>()
        var hasVoiceInChunk = false
        
        while (isRecording) {
            val readResult = audioRecord?.read(buffer, 0, buffer.size) ?: -1
            
            if (readResult > 0) {
                // Check for voice activity
                val audioSlice = buffer.take(readResult).toShortArray()
                val hasVoice = AudioUtils.hasVoiceActivity(audioSlice, VAD_THRESHOLD)
                if (hasVoice && !hasVoiceInChunk) { // Log only first detection per chunk
                    Log.d(TAG, "✅ Voice detected in chunk!")
                    hasVoiceInChunk = true
                } else if (hasVoice) {
                    hasVoiceInChunk = true
                }
                
                // Add to chunk buffer
                chunkBuffer.addAll(buffer.take(readResult))
                
                // When we have enough samples, process the chunk
                if (chunkBuffer.size >= chunkSamples) {
                    val chunk = chunkBuffer.take(chunkSamples).toShortArray()
                    chunkBuffer.clear()
                    
                    // Only upload if there was voice activity
                    if (hasVoiceInChunk) {
                        val audioFile = saveAndUploadChunk(chunk)
                        Log.d(TAG, "Processed chunk with voice: ${audioFile?.absolutePath}")
                    } else {
                        Log.d(TAG, "Skipped silent chunk")
                    }
                    
                    hasVoiceInChunk = false
                }
            } else {
                Log.e(TAG, "Error reading audio: $readResult")
            }
        }
    }
    
    private suspend fun saveAndUploadChunk(audioData: ShortArray): File? {
        return withContext(Dispatchers.IO) {
            try {
                // Save as WAV file
                val file = File(cacheDir, "chunk_${System.currentTimeMillis()}.wav")
                AudioUtils.saveAsWav(file, audioData, SAMPLE_RATE)
                Log.d(TAG, "Saved WAV file: ${file.name}, size: ${file.length()} bytes")
                
                // Get location
                val location = locationHelper.getLastLocation()
                Log.d(TAG, "Location: ${location?.latitude}, ${location?.longitude}")
                
                // Upload file to backend using multipart
                val requestFile = file.asRequestBody("audio/wav".toMediaTypeOrNull())
                val filePart = MultipartBody.Part.createFormData("file", file.name, requestFile)
                
                val deviceId = Build.MODEL.toRequestBody("text/plain".toMediaTypeOrNull())
                val lat = location?.latitude?.toString()?.toRequestBody("text/plain".toMediaTypeOrNull())
                val lon = location?.longitude?.toString()?.toRequestBody("text/plain".toMediaTypeOrNull())
                
                Log.d(TAG, "Uploading chunk to backend...")
                val response = ApiClient.api.uploadChunk(filePart, deviceId, lat, lon)
                Log.d(TAG, "✅ Chunk uploaded successfully: chunk_id=${response.chunk_id}, status=${response.status}")
                
                // Don't delete file - backend needs to keep it for transcription
                // The backend will clean up old chunks later
                
                file
            } catch (e: Exception) {
                Log.e(TAG, "❌ Error uploading chunk: ${e.message}", e)
                null
            }
        }
    }
}

