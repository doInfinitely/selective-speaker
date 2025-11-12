package ai.gauntlet.selectivespeaker.util

import java.io.File
import java.io.FileOutputStream
import java.io.IOException
import java.nio.ByteBuffer
import java.nio.ByteOrder
import kotlin.math.abs
import kotlin.math.sqrt

object AudioUtils {
    
    /**
     * Save PCM audio data as WAV file
     */
    fun saveAsWav(file: File, audioData: ShortArray, sampleRate: Int) {
        try {
            FileOutputStream(file).use { fos ->
                // Write WAV header
                val channels = 1
                val bitsPerSample = 16
                val dataSize = audioData.size * 2
                val byteRate = sampleRate * channels * bitsPerSample / 8
                
                // RIFF header
                fos.write("RIFF".toByteArray())
                fos.write(intToByteArray(36 + dataSize), 0, 4)
                fos.write("WAVE".toByteArray())
                
                // fmt chunk
                fos.write("fmt ".toByteArray())
                fos.write(intToByteArray(16), 0, 4) // fmt chunk size
                fos.write(shortToByteArray(1), 0, 2) // audio format (1 = PCM)
                fos.write(shortToByteArray(channels.toShort()), 0, 2)
                fos.write(intToByteArray(sampleRate), 0, 4)
                fos.write(intToByteArray(byteRate), 0, 4)
                fos.write(shortToByteArray((channels * bitsPerSample / 8).toShort()), 0, 2)
                fos.write(shortToByteArray(bitsPerSample.toShort()), 0, 2)
                
                // data chunk
                fos.write("data".toByteArray())
                fos.write(intToByteArray(dataSize), 0, 4)
                
                // Write audio data
                val byteBuffer = ByteBuffer.allocate(audioData.size * 2)
                byteBuffer.order(ByteOrder.LITTLE_ENDIAN)
                for (sample in audioData) {
                    byteBuffer.putShort(sample)
                }
                fos.write(byteBuffer.array())
            }
        } catch (e: IOException) {
            throw RuntimeException("Error saving WAV file", e)
        }
    }
    
    /**
     * Simple Voice Activity Detection based on energy
     */
    fun hasVoiceActivity(audioData: ShortArray, threshold: Float = 500f): Boolean {
        if (audioData.isEmpty()) return false
        
        // Calculate RMS (Root Mean Square) energy
        val rms = sqrt(audioData.map { (it * it).toDouble() }.average()).toFloat()
        
        return rms > threshold
    }
    
    /**
     * Calculate audio energy level (for visualization)
     */
    fun calculateEnergy(audioData: ShortArray): Float {
        if (audioData.isEmpty()) return 0f
        
        return audioData.map { abs(it.toFloat()) }.average().toFloat()
    }
    
    private fun intToByteArray(value: Int): ByteArray {
        return byteArrayOf(
            (value and 0xFF).toByte(),
            ((value shr 8) and 0xFF).toByte(),
            ((value shr 16) and 0xFF).toByte(),
            ((value shr 24) and 0xFF).toByte()
        )
    }
    
    private fun shortToByteArray(value: Short): ByteArray {
        return byteArrayOf(
            (value.toInt() and 0xFF).toByte(),
            ((value.toInt() shr 8) and 0xFF).toByte()
        )
    }
}

