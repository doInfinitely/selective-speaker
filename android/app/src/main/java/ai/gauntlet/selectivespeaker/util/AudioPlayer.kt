package ai.gauntlet.selectivespeaker.util

import android.content.Context
import android.media.AudioManager
import android.media.MediaPlayer
import android.util.Log
import ai.gauntlet.selectivespeaker.api.ApiClient
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.File
import java.io.FileOutputStream

object AudioPlayer {
    
    private const val TAG = "AudioPlayer"
    private var mediaPlayer: MediaPlayer? = null
    
    suspend fun playUtterance(context: Context, utteranceId: Int) {
        withContext(Dispatchers.IO) {
            try {
                // Stop any currently playing audio
                stop()
                
                // Download audio from backend
                val response = ApiClient.api.getUtteranceAudio(utteranceId)
                val audioBytes = response.bytes()
                
                // Save to temp file
                val tempFile = File(context.cacheDir, "utterance_${utteranceId}.wav")
                FileOutputStream(tempFile).use { fos ->
                    fos.write(audioBytes)
                }
                
                // Play audio
                withContext(Dispatchers.Main) {
                    mediaPlayer = MediaPlayer().apply {
                        // Set audio stream type to MUSIC for better volume control
                        setAudioStreamType(AudioManager.STREAM_MUSIC)
                        
                        setDataSource(tempFile.absolutePath)
                        prepare()
                        
                        // Set volume to maximum (1.0f for both left and right channels)
                        setVolume(1.0f, 1.0f)
                        
                        setOnCompletionListener {
                            stop()
                            tempFile.delete()
                        }
                        start()
                    }
                    
                    Log.d(TAG, "Playing at full volume")
                }
                
                Log.d(TAG, "Playing utterance $utteranceId")
                
            } catch (e: Exception) {
                Log.e(TAG, "Error playing audio", e)
                throw e
            }
        }
    }
    
    fun stop() {
        mediaPlayer?.apply {
            if (isPlaying) {
                stop()
            }
            release()
        }
        mediaPlayer = null
    }
}

