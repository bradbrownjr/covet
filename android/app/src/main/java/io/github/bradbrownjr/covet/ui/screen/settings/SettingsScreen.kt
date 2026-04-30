package io.github.bradbrownjr.covet.ui.screen.settings

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.launch
import io.github.bradbrownjr.covet.data.auth.SessionStore
import io.github.bradbrownjr.covet.data.repo.AuthRepository
import javax.inject.Inject

data class SettingsUi(
    val baseUrl: String? = null,
    val username: String? = null,
    val testBusy: Boolean = false,
    val testResult: String? = null,
    val testOk: Boolean = false,
    // "system" | "light" | "dark" — null treated as "system"
    val themeMode: String? = null,
)

@HiltViewModel
class SettingsViewModel @Inject constructor(
    private val session: SessionStore,
    private val auth: AuthRepository,
) : ViewModel() {
    private val _state = MutableStateFlow(SettingsUi())
    val state: StateFlow<SettingsUi> = _state.asStateFlow()

    init {
        viewModelScope.launch {
            session.baseUrl.combine(session.username) { url, name -> url to name }
                .collect { (url, name) ->
                    _state.value = _state.value.copy(baseUrl = url, username = name)
                }
        }
        viewModelScope.launch {
            session.themeMode.collect { mode ->
                _state.value = _state.value.copy(themeMode = mode)
            }
        }
    }

    fun signOut(after: () -> Unit) {
        viewModelScope.launch { auth.logout(); after() }
    }

    fun setTheme(mode: String) {
        viewModelScope.launch { session.saveTheme(mode) }
    }

    fun testConnection() {
        val url = _state.value.baseUrl ?: return
        if (_state.value.testBusy) return
        _state.value = _state.value.copy(testBusy = true, testResult = null)
        viewModelScope.launch {
            val (msg, ok) = try {
                auth.testConnection(url)
                Pair("Connected successfully", true)
            } catch (t: Throwable) {
                Pair(t.message ?: "Connection failed", false)
            }
            _state.value = _state.value.copy(testBusy = false, testResult = msg, testOk = ok)
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SettingsScreen(
    onSignOut: () -> Unit,
    onBack: () -> Unit,
    vm: SettingsViewModel = hiltViewModel(),
) {
    val s by vm.state.collectAsState()
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Settings") },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
                    }
                },
            )
        }
    ) { padding ->
        Column(
            Modifier.fillMaxSize().padding(padding).padding(24.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Text("Server: ${s.baseUrl ?: "—"}")
            Text("Signed in as: ${s.username ?: "—"}")
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                OutlinedButton(
                    onClick = vm::testConnection,
                    enabled = !s.testBusy && s.baseUrl != null,
                ) {
                    if (s.testBusy) {
                        CircularProgressIndicator(Modifier.size(16.dp), strokeWidth = 2.dp)
                    } else {
                        Text("Test connection")
                    }
                }
                if (s.testResult != null) {
                    Text(
                        text = s.testResult!!,
                        color = if (s.testOk) Color(0xFF2E7D32) else MaterialTheme.colorScheme.error,
                        style = MaterialTheme.typography.bodySmall,
                    )
                }
            }
            HorizontalDivider()
            Text("Appearance", style = MaterialTheme.typography.labelMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant)
            @OptIn(ExperimentalMaterial3Api::class)
            SingleChoiceSegmentedButtonRow {
                val options = listOf("system" to "System", "light" to "Light", "dark" to "Dark")
                options.forEachIndexed { index, (value, label) ->
                    SegmentedButton(
                        selected = (s.themeMode ?: "system") == value,
                        onClick = { vm.setTheme(value) },
                        shape = SegmentedButtonDefaults.itemShape(index = index, count = options.size),
                        label = { Text(label) },
                    )
                }
            }
            HorizontalDivider()
            Button(onClick = { vm.signOut(onSignOut) }) { Text("Sign out") }
        }
    }
}
