package ai.gauntlet.selectivespeaker.ui

import android.content.Intent
import android.os.Bundle
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import ai.gauntlet.selectivespeaker.R
import ai.gauntlet.selectivespeaker.auth.AuthManager
import ai.gauntlet.selectivespeaker.databinding.ActivitySignInBinding
import kotlinx.coroutines.launch

class SignInActivity : AppCompatActivity() {
    
    private lateinit var binding: ActivitySignInBinding
    private var isSignUpMode = false
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        // Check if already signed in
        if (AuthManager.isSignedIn()) {
            navigateToMain()
            return
        }
        
        binding = ActivitySignInBinding.inflate(layoutInflater)
        setContentView(binding.root)
        
        setupClickListeners()
    }
    
    private fun setupClickListeners() {
        binding.buttonSignIn.setOnClickListener {
            val email = binding.editTextEmail.text.toString().trim()
            val password = binding.editTextPassword.text.toString()
            
            if (validateInput(email, password)) {
                if (isSignUpMode) {
                    signUp(email, password)
                } else {
                    signIn(email, password)
                }
            }
        }
        
        binding.textViewToggleMode.setOnClickListener {
            toggleMode()
        }
    }
    
    private fun validateInput(email: String, password: String): Boolean {
        if (email.isEmpty()) {
            binding.editTextEmail.error = "Email required"
            return false
        }
        
        if (!android.util.Patterns.EMAIL_ADDRESS.matcher(email).matches()) {
            binding.editTextEmail.error = "Invalid email"
            return false
        }
        
        if (password.isEmpty()) {
            binding.editTextPassword.error = "Password required"
            return false
        }
        
        if (password.length < 6) {
            binding.editTextPassword.error = "Password must be at least 6 characters"
            return false
        }
        
        return true
    }
    
    private fun signIn(email: String, password: String) {
        binding.buttonSignIn.isEnabled = false
        binding.progressBar.visibility = android.view.View.VISIBLE
        
        lifecycleScope.launch {
            val result = AuthManager.signIn(email, password)
            
            binding.buttonSignIn.isEnabled = true
            binding.progressBar.visibility = android.view.View.GONE
            
            result.onSuccess {
                Toast.makeText(this@SignInActivity, "Sign in successful!", Toast.LENGTH_SHORT).show()
                navigateToMain()
            }.onFailure { error ->
                Toast.makeText(
                    this@SignInActivity,
                    "Sign in failed: ${error.message}",
                    Toast.LENGTH_LONG
                ).show()
            }
        }
    }
    
    private fun signUp(email: String, password: String) {
        binding.buttonSignIn.isEnabled = false
        binding.progressBar.visibility = android.view.View.VISIBLE
        
        lifecycleScope.launch {
            val result = AuthManager.signUp(email, password)
            
            binding.buttonSignIn.isEnabled = true
            binding.progressBar.visibility = android.view.View.GONE
            
            result.onSuccess {
                Toast.makeText(this@SignInActivity, "Account created successfully!", Toast.LENGTH_SHORT).show()
                navigateToMain()
            }.onFailure { error ->
                Toast.makeText(
                    this@SignInActivity,
                    "Sign up failed: ${error.message}",
                    Toast.LENGTH_LONG
                ).show()
            }
        }
    }
    
    private fun toggleMode() {
        isSignUpMode = !isSignUpMode
        
        if (isSignUpMode) {
            binding.buttonSignIn.text = "Sign Up"
            binding.textViewToggleMode.text = "Already have an account? Sign In"
        } else {
            binding.buttonSignIn.text = "Sign In"
            binding.textViewToggleMode.text = "Don't have an account? Sign Up"
        }
    }
    
    private fun navigateToMain() {
        val intent = Intent(this, MainActivity::class.java)
        intent.flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
        startActivity(intent)
        finish()
    }
}

