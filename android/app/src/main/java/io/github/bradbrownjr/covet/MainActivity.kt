package io.github.bradbrownjr.covet

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import dagger.hilt.android.AndroidEntryPoint
import io.github.bradbrownjr.covet.data.auth.SessionStore
import io.github.bradbrownjr.covet.ui.CovetApp
import io.github.bradbrownjr.covet.ui.theme.CovetTheme
import javax.inject.Inject

@AndroidEntryPoint
class MainActivity : ComponentActivity() {
    @Inject lateinit var sessionStore: SessionStore

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            val themeMode by sessionStore.themeMode.collectAsState(initial = null)
            val systemDark = isSystemInDarkTheme()
            val dark = when (themeMode) {
                "light" -> false
                "dark"  -> true
                else    -> systemDark
            }
            CovetTheme(darkTheme = dark) {
                CovetApp()
            }
        }
    }
}
