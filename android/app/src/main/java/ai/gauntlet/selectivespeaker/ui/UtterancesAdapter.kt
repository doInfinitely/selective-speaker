package ai.gauntlet.selectivespeaker.ui

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import ai.gauntlet.selectivespeaker.api.Utterance
import ai.gauntlet.selectivespeaker.databinding.ItemUtteranceBinding

class UtterancesAdapter(
    private val onPlayClick: (Utterance) -> Unit
) : ListAdapter<Utterance, UtterancesAdapter.ViewHolder>(UtteranceDiffCallback()) {
    
    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val binding = ItemUtteranceBinding.inflate(
            LayoutInflater.from(parent.context),
            parent,
            false
        )
        return ViewHolder(binding, onPlayClick)
    }
    
    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        holder.bind(getItem(position))
    }
    
    class ViewHolder(
        private val binding: ItemUtteranceBinding,
        private val onPlayClick: (Utterance) -> Unit
    ) : RecyclerView.ViewHolder(binding.root) {
        
        fun bind(utterance: Utterance) {
            binding.textViewUtterance.text = utterance.text
            binding.textViewDuration.text = "${(utterance.end_ms - utterance.start_ms) / 1000.0}s"
            binding.textViewTimestamp.text = utterance.timestamp ?: ""
            
            binding.buttonPlay.setOnClickListener {
                onPlayClick(utterance)
            }
        }
    }
}

class UtteranceDiffCallback : DiffUtil.ItemCallback<Utterance>() {
    override fun areItemsTheSame(oldItem: Utterance, newItem: Utterance): Boolean {
        return oldItem.id == newItem.id
    }
    
    override fun areContentsTheSame(oldItem: Utterance, newItem: Utterance): Boolean {
        return oldItem == newItem
    }
}

