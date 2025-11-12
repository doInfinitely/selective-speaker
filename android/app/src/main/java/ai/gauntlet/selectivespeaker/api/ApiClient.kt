package ai.gauntlet.selectivespeaker.api

import ai.gauntlet.selectivespeaker.BuildConfig
import ai.gauntlet.selectivespeaker.auth.AuthManager
import okhttp3.Interceptor
import okhttp3.MultipartBody
import okhttp3.OkHttpClient
import okhttp3.RequestBody
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.*
import java.util.concurrent.TimeUnit

/**
 * Data models for API requests/responses
 */
data class EnrollmentRequest(
    val audio_url: String,
    val duration_ms: Int,
    val phrase_text: String?
)

data class EnrollmentResponse(
    val status: String,
    val enrollment_id: Int,
    val user_id: Int,
    val embedding_dimensions: Int?
)

data class EnrollmentStatusResponse(
    val enrolled: Boolean,
    val enrollment_id: Int? = null,
    val duration_ms: Int? = null,
    val created_at: String? = null
)

data class ChunkSubmitRequest(
    val audio_url: String,
    val device_id: String?,
    val start_ts: String?,
    val end_ts: String?,
    val gps_lat: Double?,
    val gps_lon: Double?
)

data class ChunkSubmitResponse(
    val status: String,
    val chunk_id: Int,
    val enrollment_id: Int?,
    val message: String?
)

data class Utterance(
    val id: Int,
    val chunk_id: Int,
    val start_ms: Int,
    val end_ms: Int,
    val text: String,
    val device_id: String?,
    val timestamp: String?,
    val address: String?
)

data class UtterancesResponse(
    val items: List<Utterance>,
    val count: Int,
    val has_more: Boolean
)

/**
 * Retrofit API interface
 */
interface SelectiveSpeakerApi {
    
    @POST("enrollment/complete")
    suspend fun completeEnrollment(@Body request: EnrollmentRequest): EnrollmentResponse
    
    @Multipart
    @POST("enrollment/upload")
    suspend fun uploadEnrollment(
        @Part file: MultipartBody.Part,
        @Part("duration_ms") durationMs: RequestBody,
        @Part("phrase_text") phraseText: RequestBody?
    ): EnrollmentResponse
    
    @GET("enrollment/status")
    suspend fun enrollmentStatus(): EnrollmentStatusResponse
    
    @POST("chunks/submit")
    suspend fun submitChunk(@Body request: ChunkSubmitRequest): ChunkSubmitResponse
    
    @Multipart
    @POST("chunks/upload")
    suspend fun uploadChunk(
        @Part file: MultipartBody.Part,
        @Part("device_id") deviceId: RequestBody?,
        @Part("gps_lat") lat: RequestBody?,
        @Part("gps_lon") lon: RequestBody?
    ): ChunkSubmitResponse
    
    @GET("utterances")
    suspend fun getUtterances(
        @Query("limit") limit: Int = 50,
        @Query("offset") offset: Int = 0
    ): UtterancesResponse
    
    @GET("audio/utterances/{id}")
    suspend fun getUtteranceAudio(@Path("id") utteranceId: Int): okhttp3.ResponseBody
}

/**
 * API client singleton
 */
object ApiClient {
    
    private val authInterceptor = Interceptor { chain ->
        val originalRequest = chain.request()
        
        // Get the Firebase ID token (cached, might be slightly outdated but usually fine)
        val token = AuthManager.getCachedIdToken()
        
        // Add Authorization header if token exists
        val newRequest = if (token != null) {
            originalRequest.newBuilder()
                .addHeader("Authorization", "Bearer $token")
                .build()
        } else {
            originalRequest
        }
        
        chain.proceed(newRequest)
    }
    
    private val loggingInterceptor = HttpLoggingInterceptor().apply {
        level = if (BuildConfig.DEBUG) {
            HttpLoggingInterceptor.Level.BODY
        } else {
            HttpLoggingInterceptor.Level.NONE
        }
    }
    
    private val okHttpClient = OkHttpClient.Builder()
        .addInterceptor(authInterceptor)  // Add auth first
        .addInterceptor(loggingInterceptor)
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .writeTimeout(30, TimeUnit.SECONDS)
        .build()
    
    private val retrofit = Retrofit.Builder()
        .baseUrl(BuildConfig.API_BASE_URL)
        .client(okHttpClient)
        .addConverterFactory(GsonConverterFactory.create())
        .build()
    
    val api: SelectiveSpeakerApi = retrofit.create(SelectiveSpeakerApi::class.java)
}

