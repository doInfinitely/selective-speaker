package ai.gauntlet.selectivespeaker

import android.app.Application
import android.app.NotificationChannel
import android.app.NotificationManager
import android.os.Build
import ai.gauntlet.selectivespeaker.auth.AuthManager

class SelectiveSpeakerApp : Application() {
    
    companion object {
        const val NOTIFICATION_CHANNEL_ID = "recording_channel"
        const val NOTIFICATION_CHANNEL_NAME = "Recording Service"
    }
    
    override fun onCreate() {
        super.onCreate()
        
        // Initialize authentication manager
        AuthManager.initialize(this)
        
        createNotificationChannel()
    }
    
    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                NOTIFICATION_CHANNEL_ID,
                NOTIFICATION_CHANNEL_NAME,
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "Continuous audio recording notification"
                setShowBadge(false)
            }
            
            val notificationManager = getSystemService(NotificationManager::class.java)
            notificationManager.createNotificationChannel(channel)
        }
    }
}

