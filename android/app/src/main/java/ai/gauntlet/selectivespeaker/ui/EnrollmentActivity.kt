package ai.gauntlet.selectivespeaker.ui

import android.Manifest
import android.content.pm.PackageManager
import android.media.AudioFormat
import android.media.AudioRecord
import android.media.MediaRecorder
import android.os.Bundle
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.lifecycle.lifecycleScope
import ai.gauntlet.selectivespeaker.api.ApiClient
import ai.gauntlet.selectivespeaker.api.EnrollmentRequest
import ai.gauntlet.selectivespeaker.databinding.ActivityEnrollmentBinding
import ai.gauntlet.selectivespeaker.util.AudioUtils
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.asRequestBody
import okhttp3.RequestBody.Companion.toRequestBody
import java.io.File
import java.io.FileOutputStream

class EnrollmentActivity : AppCompatActivity() {
    
    private lateinit var binding: ActivityEnrollmentBinding
    private var audioRecord: AudioRecord? = null
    private var isRecording = false
    private var recordedFile: File? = null
    private val audioBuffer = mutableListOf<Short>()
    
    companion object {
        private const val SAMPLE_RATE = 16000
        private const val ENROLLMENT_DURATION_MS = 15000 // 15 seconds
    }
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityEnrollmentBinding.inflate(layoutInflater)
        setContentView(binding.root)
        
        setupUI()
    }
    
    private fun setupUI() {
        binding.textViewInstructions.text = """
            Please read the following phrase clearly:
            
            "The quick brown fox jumps over the lazy dog. 
            I authorize this device to record my voice for selective transcription."
            
            This helps us learn your voice pattern.
        """.trimIndent()
        
        binding.buttonStartRecording.setOnClickListener {
            if (isRecording) {
                stopRecording()
            } else {
                startRecording()
            }
        }
        
        binding.buttonSubmit.setOnClickListener {
            submitEnrollment()
        }
        
        binding.buttonSubmit.isEnabled = false
    }
    
    private fun startRecording() {
        if (ActivityCompat.checkSelfPermission(
                this,
                Manifest.permission.RECORD_AUDIO
            ) != PackageManager.PERMISSION_GRANTED
        ) {
            Toast.makeText(this, "Microphone permission required", Toast.LENGTH_SHORT).show()
            return
        }
        
        val bufferSize = AudioRecord.getMinBufferSize(
            SAMPLE_RATE,
            AudioFormat.CHANNEL_IN_MONO,
            AudioFormat.ENCODING_PCM_16BIT
        )
        
        audioRecord = AudioRecord(
            MediaRecorder.AudioSource.VOICE_RECOGNITION,
            SAMPLE_RATE,
            AudioFormat.CHANNEL_IN_MONO,
            AudioFormat.ENCODING_PCM_16BIT,
            bufferSize
        )
        
        isRecording = true
        audioBuffer.clear()
        audioRecord?.startRecording()
        
        binding.buttonStartRecording.text = "Recording... (${ENROLLMENT_DURATION_MS / 1000}s)"
        binding.progressBar.max = ENROLLMENT_DURATION_MS
        binding.progressBar.progress = 0
        
        lifecycleScope.launch(Dispatchers.IO) {
            recordAudio()
        }
    }
    
    private suspend fun recordAudio() {
        val buffer = ShortArray(1024)
        val startTime = System.currentTimeMillis()
        
        while (isRecording && (System.currentTimeMillis() - startTime) < ENROLLMENT_DURATION_MS) {
            val read = audioRecord?.read(buffer, 0, buffer.size) ?: 0
            if (read > 0) {
                audioBuffer.addAll(buffer.take(read))
                
                withContext(Dispatchers.Main) {
                    val elapsed = (System.currentTimeMillis() - startTime).toInt()
                    binding.progressBar.progress = elapsed
                    val remaining = (ENROLLMENT_DURATION_MS - elapsed) / 1000
                    binding.buttonStartRecording.text = "Recording... (${remaining}s)"
                }
            }
        }
        
        stopRecording()
    }
    
    private fun stopRecording() {
        isRecording = false
        audioRecord?.stop()
        audioRecord?.release()
        audioRecord = null
        
        runOnUiThread {
            binding.buttonStartRecording.text = "Re-record"
            binding.buttonSubmit.isEnabled = audioBuffer.isNotEmpty()
            
            if (audioBuffer.isNotEmpty()) {
                // Save to file
                recordedFile = File(cacheDir, "enrollment_${System.currentTimeMillis()}.wav")
                AudioUtils.saveAsWav(recordedFile!!, audioBuffer.toShortArray(), SAMPLE_RATE)
                Toast.makeText(this@EnrollmentActivity, "Recording complete! Ready to submit.", Toast.LENGTH_SHORT).show()
            }
        }
    }
    
    private fun submitEnrollment() {
        val file = recordedFile ?: return
        
        binding.progressBar.isIndeterminate = true
        binding.buttonSubmit.isEnabled = false
        
        lifecycleScope.launch(Dispatchers.IO) {
            try {
                // Upload file using multipart
                val requestFile = file.asRequestBody("audio/wav".toMediaTypeOrNull())
                val filePart = MultipartBody.Part.createFormData("file", file.name, requestFile)
                
                val durationMs = ENROLLMENT_DURATION_MS.toString().toRequestBody("text/plain".toMediaTypeOrNull())
                val phraseText = "The quick brown fox jumps over the lazy dog".toRequestBody("text/plain".toMediaTypeOrNull())
                
                val response = ApiClient.api.uploadEnrollment(filePart, durationMs, phraseText)
                
                withContext(Dispatchers.Main) {
                    Toast.makeText(
                        this@EnrollmentActivity,
                        "Enrollment successful! Embedding extracted: ${response.embedding_dimensions} dims",
                        Toast.LENGTH_LONG
                    ).show()
                    finish()
                }
                
            } catch (e: Exception) {
                withContext(Dispatchers.Main) {
                    binding.progressBar.isIndeterminate = false
                    binding.buttonSubmit.isEnabled = true
                    Toast.makeText(
                        this@EnrollmentActivity,
                        "Error: ${e.message}",
                        Toast.LENGTH_LONG
                    ).show()
                }
            }
        }
    }
    
    override fun onDestroy() {
        // Stop recording synchronously if needed
        if (isRecording) {
            isRecording = false
            audioRecord?.stop()
            audioRecord?.release()
            audioRecord = null
        }
        super.onDestroy()
    }
}

