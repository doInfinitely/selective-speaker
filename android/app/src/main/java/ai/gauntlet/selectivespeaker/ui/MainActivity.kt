package ai.gauntlet.selectivespeaker.ui

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.view.Menu
import android.view.MenuItem
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import ai.gauntlet.selectivespeaker.R
import ai.gauntlet.selectivespeaker.api.ApiClient
import ai.gauntlet.selectivespeaker.auth.AuthManager
import ai.gauntlet.selectivespeaker.databinding.ActivityMainBinding
import ai.gauntlet.selectivespeaker.service.RecordingService
import kotlinx.coroutines.launch

class MainActivity : AppCompatActivity() {
    
    companion object {
        private const val TAG = "MainActivity"
        private const val PERMISSION_REQUEST_CODE = 100
        private val REQUIRED_PERMISSIONS = arrayOf(
            Manifest.permission.RECORD_AUDIO,
            Manifest.permission.ACCESS_FINE_LOCATION,
            Manifest.permission.POST_NOTIFICATIONS
        )
    }
    
    private lateinit var binding: ActivityMainBinding
    private lateinit var utterancesAdapter: UtterancesAdapter
    private var isRecording = false
    private var hasEnrolled = false
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)
        
        setupRecyclerView()
        setupClickListeners()
        checkPermissions()
    }
    
    private fun setupRecyclerView() {
        utterancesAdapter = UtterancesAdapter(
            onPlayClick = { utterance ->
                lifecycleScope.launch {
                    try {
                        Toast.makeText(
                            this@MainActivity,
                            "Playing: ${utterance.text}",
                            Toast.LENGTH_SHORT
                        ).show()
                        
                        ai.gauntlet.selectivespeaker.util.AudioPlayer.playUtterance(
                            this@MainActivity,
                            utterance.id
                        )
                    } catch (e: Exception) {
                        Toast.makeText(
                            this@MainActivity,
                            "Error playing audio: ${e.message}",
                            Toast.LENGTH_LONG
                        ).show()
                    }
                }
            }
        )
        
        binding.recyclerViewUtterances.apply {
            layoutManager = LinearLayoutManager(this@MainActivity)
            adapter = utterancesAdapter
        }
    }
    
    private fun setupClickListeners() {
        binding.buttonEnroll.setOnClickListener {
            startActivity(Intent(this, EnrollmentActivity::class.java))
        }
        
        binding.buttonToggleRecording.setOnClickListener {
            if (isRecording) {
                stopRecording()
            } else {
                startRecording()
            }
        }
        
        binding.buttonRefresh.setOnClickListener {
            loadUtterances()
        }
    }
    
    override fun onResume() {
        super.onResume()
        loadUtterances()
    }
    
    private fun checkPermissions() {
        val permissionsToRequest = REQUIRED_PERMISSIONS.filter {
            ContextCompat.checkSelfPermission(this, it) != PackageManager.PERMISSION_GRANTED
        }
        
        if (permissionsToRequest.isNotEmpty()) {
            ActivityCompat.requestPermissions(
                this,
                permissionsToRequest.toTypedArray(),
                PERMISSION_REQUEST_CODE
            )
        }
    }
    
    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<out String>,
        grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        
        if (requestCode == PERMISSION_REQUEST_CODE) {
            val allGranted = grantResults.all { it == PackageManager.PERMISSION_GRANTED }
            if (!allGranted) {
                Toast.makeText(
                    this,
                    "Permissions required for recording",
                    Toast.LENGTH_LONG
                ).show()
            }
        }
    }
    
    private fun startRecording() {
        val intent = Intent(this, RecordingService::class.java)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            startForegroundService(intent)
        } else {
            startService(intent)
        }
        
        isRecording = true
        binding.buttonToggleRecording.text = "Stop Recording"
        Toast.makeText(this, "Recording started", Toast.LENGTH_SHORT).show()
    }
    
    private fun stopRecording() {
        val intent = Intent(this, RecordingService::class.java)
        stopService(intent)
        
        isRecording = false
        binding.buttonToggleRecording.text = "Start Recording"
        Toast.makeText(this, "Recording stopped", Toast.LENGTH_SHORT).show()
    }
    
    private fun loadUtterances() {
        lifecycleScope.launch {
            try {
                binding.progressBar.visibility = android.view.View.VISIBLE
                val response = ApiClient.api.getUtterances(limit = 50)
                utterancesAdapter.submitList(response.items)
                binding.textViewCount.text = "Total: ${response.count} utterances"
                
                // Scroll to top to show newest utterances
                if (response.items.isNotEmpty()) {
                    binding.recyclerViewUtterances.smoothScrollToPosition(0)
                }
                
                binding.progressBar.visibility = android.view.View.GONE
            } catch (e: Exception) {
                binding.progressBar.visibility = android.view.View.GONE
                Toast.makeText(
                    this@MainActivity,
                    "Error loading utterances: ${e.message}",
                    Toast.LENGTH_LONG
                ).show()
            }
        }
    }
    
    override fun onCreateOptionsMenu(menu: Menu?): Boolean {
        menuInflater.inflate(R.menu.main_menu, menu)
        return true
    }
    
    override fun onOptionsItemSelected(item: MenuItem): Boolean {
        return when (item.itemId) {
            R.id.action_sign_out -> {
                signOut()
                true
            }
            else -> super.onOptionsItemSelected(item)
        }
    }
    
    private fun signOut() {
        // Stop recording if active
        if (isRecording) {
            stopRecording()
        }
        
        // Sign out
        AuthManager.signOut()
        
        // Navigate to sign-in activity
        val intent = Intent(this, SignInActivity::class.java)
        intent.flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
        startActivity(intent)
        finish()
    }
}

