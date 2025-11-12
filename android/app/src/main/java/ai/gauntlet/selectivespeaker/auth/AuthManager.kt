package ai.gauntlet.selectivespeaker.auth

import android.content.Context
import android.content.SharedPreferences
import com.google.firebase.auth.FirebaseAuth
import com.google.firebase.auth.FirebaseUser
import kotlinx.coroutines.tasks.await

/**
 * Manages Firebase authentication and token storage.
 */
object AuthManager {
    
    private const val PREFS_NAME = "selective_speaker_auth"
    private const val KEY_ID_TOKEN = "firebase_id_token"
    
    private lateinit var prefs: SharedPreferences
    private val auth: FirebaseAuth = FirebaseAuth.getInstance()
    
    fun initialize(context: Context) {
        prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
    }
    
    /**
     * Get the current Firebase user.
     */
    fun getCurrentUser(): FirebaseUser? {
        return auth.currentUser
    }
    
    /**
     * Check if user is signed in.
     */
    fun isSignedIn(): Boolean {
        return auth.currentUser != null
    }
    
    /**
     * Sign in with email and password.
     */
    suspend fun signIn(email: String, password: String): Result<FirebaseUser> {
        return try {
            val result = auth.signInWithEmailAndPassword(email, password).await()
            val user = result.user ?: return Result.failure(Exception("Sign in failed: No user"))
            
            // Get and store ID token
            val token = user.getIdToken(false).await().token
            if (token != null) {
                saveIdToken(token)
            }
            
            Result.success(user)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    /**
     * Sign up with email and password.
     */
    suspend fun signUp(email: String, password: String): Result<FirebaseUser> {
        return try {
            val result = auth.createUserWithEmailAndPassword(email, password).await()
            val user = result.user ?: return Result.failure(Exception("Sign up failed: No user"))
            
            // Get and store ID token
            val token = user.getIdToken(false).await().token
            if (token != null) {
                saveIdToken(token)
            }
            
            Result.success(user)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    /**
     * Sign out the current user.
     */
    fun signOut() {
        auth.signOut()
        clearIdToken()
    }
    
    /**
     * Get the current Firebase ID token.
     * Refreshes it if needed.
     */
    suspend fun getIdToken(forceRefresh: Boolean = false): String? {
        val user = auth.currentUser ?: return null
        
        return try {
            val result = user.getIdToken(forceRefresh).await()
            val token = result.token
            if (token != null) {
                saveIdToken(token)
            }
            token
        } catch (e: Exception) {
            null
        }
    }
    
    /**
     * Get the cached ID token (might be expired).
     */
    fun getCachedIdToken(): String? {
        return prefs.getString(KEY_ID_TOKEN, null)
    }
    
    /**
     * Save ID token to SharedPreferences.
     */
    private fun saveIdToken(token: String) {
        prefs.edit().putString(KEY_ID_TOKEN, token).apply()
    }
    
    /**
     * Clear stored ID token.
     */
    private fun clearIdToken() {
        prefs.edit().remove(KEY_ID_TOKEN).apply()
    }
}

