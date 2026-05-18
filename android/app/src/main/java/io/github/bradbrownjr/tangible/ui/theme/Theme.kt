package io.github.bradbrownjr.tangible.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

// ── Helper ────────────────────────────────────────────────────────────────────
private fun hex(s: String): Color = Color(android.graphics.Color.parseColor(s))

// ── Palette metadata (drives the swatch picker in Settings) ──────────────────
data class AppPalette(
    val id: String,
    val name: String,
    val darkBg: Color,
    val darkAccent: Color,
    val lightBg: Color,
    val lightAccent: Color,
)

val ALL_PALETTES: List<AppPalette> = listOf(
    AppPalette("blackboard", "Blackboard", hex("#1A1A1A"), hex("#FFB347"), hex("#FDFCF8"), hex("#C26800")),
    AppPalette("blues",      "Blues",      hex("#2B2C56"), hex("#6677EB"), hex("#EEF0FF"), hex("#4338CA")),
    AppPalette("cloud",      "Cloud",      hex("#1A2328"), hex("#37BBE4"), hex("#F1F2F0"), hex("#37BBE4")),
    AppPalette("espresso",   "Espresso",   hex("#21211F"), hex("#C49A6C"), hex("#FDF8F0"), hex("#8B6339")),
    AppPalette("gazette",    "Gazette",    hex("#1A2030"), hex("#60A5FA"), hex("#F2F7FF"), hex("#3B82F6")),
    AppPalette("granite",    "Granite",    hex("#1D2327"), hex("#22A88E"), hex("#ECF2EF"), hex("#0F7A65")),
    AppPalette("onedark",    "One Dark",   hex("#282C34"), hex("#98C379"), hex("#F2F7EE"), hex("#3A7A22")),
    AppPalette("paper",      "Paper",      hex("#1E1C18"), hex("#C4A97A"), hex("#F8F6F1"), hex("#AA9A73")),
    AppPalette("passion",    "Passion",    hex("#1A0A2E"), hex("#CE93D8"), hex("#F5F5F5"), hex("#8E24AA")),
    AppPalette("tangible",   "Tangible",   hex("#1A1D29"), hex("#A78BFA"), hex("#F7F6FF"), hex("#7C3AED")),
    AppPalette("tron",       "Tron",       hex("#242B33"), hex("#6EE2FF"), hex("#EAF8FD"), hex("#0891B2")),
)

const val DEFAULT_PALETTE_ID = "granite"

// ── Color schemes ─────────────────────────────────────────────────────────────

private val BlackboardDark = darkColorScheme(
    primary = hex("#FFB347"), onPrimary = hex("#1A1A1A"),
    primaryContainer = hex("#303030"), onPrimaryContainer = hex("#FFFDEA"),
    secondary = hex("#76B8D4"), onSecondary = hex("#1A1A1A"),
    tertiary = hex("#7EC86C"), onTertiary = hex("#1A1A1A"),
    background = hex("#1A1A1A"), onBackground = hex("#FFFDEA"),
    surface = hex("#252525"), onSurface = hex("#FFFDEA"),
    surfaceVariant = hex("#303030"), onSurfaceVariant = hex("#AAAA90"),
    error = hex("#E05252"), onError = Color.White,
    outline = hex("#444444"),
)
private val BlackboardLight = lightColorScheme(
    primary = hex("#C26800"), onPrimary = Color.White,
    primaryContainer = hex("#FFF3E0"), onPrimaryContainer = hex("#3A1A00"),
    secondary = hex("#1E40AF"), onSecondary = Color.White,
    tertiary = hex("#4D7C0F"), onTertiary = Color.White,
    background = hex("#FDFCF8"), onBackground = hex("#1A1A1A"),
    surface = hex("#FFFFFF"), onSurface = hex("#1A1A1A"),
    surfaceVariant = hex("#EEE8DC"), onSurfaceVariant = hex("#5A4A30"),
    error = hex("#B45309"), onError = Color.White,
    outline = hex("#C8BCA8"),
)

private val BluesDark = darkColorScheme(
    primary = hex("#6677EB"), onPrimary = Color.White,
    primaryContainer = hex("#3F4090"), onPrimaryContainer = hex("#EFF1FC"),
    secondary = hex("#64B5F6"), onSecondary = hex("#2B2C56"),
    tertiary = hex("#81C784"), onTertiary = hex("#2B2C56"),
    background = hex("#2B2C56"), onBackground = hex("#EFF1FC"),
    surface = hex("#35367A"), onSurface = hex("#EFF1FC"),
    surfaceVariant = hex("#3F4090"), onSurfaceVariant = hex("#A0A5CC"),
    error = hex("#F06292"), onError = hex("#2B2C56"),
    outline = hex("#5558A8"),
)
private val BluesLight = lightColorScheme(
    primary = hex("#4338CA"), onPrimary = Color.White,
    primaryContainer = hex("#DDE0FF"), onPrimaryContainer = hex("#0A0A3A"),
    secondary = hex("#0284C7"), onSecondary = Color.White,
    tertiary = hex("#16A34A"), onTertiary = Color.White,
    background = hex("#EEF0FF"), onBackground = hex("#0A0A3A"),
    surface = hex("#FFFFFF"), onSurface = hex("#0A0A3A"),
    surfaceVariant = hex("#DDE0FF"), onSurfaceVariant = hex("#3A42A0"),
    error = hex("#DC2626"), onError = Color.White,
    outline = hex("#C0C8FF"),
)

private val CloudDark = darkColorScheme(
    primary = hex("#37BBE4"), onPrimary = hex("#0D1C22"),
    primaryContainer = hex("#283640"), onPrimaryContainer = hex("#E0F2F8"),
    secondary = hex("#60A5FA"), onSecondary = hex("#0D1C22"),
    tertiary = hex("#4ADE80"), onTertiary = hex("#0D1C22"),
    background = hex("#1A2328"), onBackground = hex("#E0F2F8"),
    surface = hex("#222D34"), onSurface = hex("#E0F2F8"),
    surfaceVariant = hex("#283640"), onSurfaceVariant = hex("#6B9BAA"),
    error = hex("#F87171"), onError = Color.White,
    outline = hex("#35474F"),
)
private val CloudLight = lightColorScheme(
    primary = hex("#37BBE4"), onPrimary = Color.White,
    primaryContainer = hex("#E3E8E6"), onPrimaryContainer = hex("#35342F"),
    secondary = hex("#0284C7"), onSecondary = Color.White,
    tertiary = hex("#16A34A"), onTertiary = Color.White,
    background = hex("#F1F2F0"), onBackground = hex("#35342F"),
    surface = hex("#FFFFFF"), onSurface = hex("#35342F"),
    surfaceVariant = hex("#E3E8E6"), onSurfaceVariant = hex("#5E6660"),
    error = hex("#DC2626"), onError = Color.White,
    outline = hex("#CAD5D0"),
)

private val EspressoDark = darkColorScheme(
    primary = hex("#C49A6C"), onPrimary = hex("#21211F"),
    primaryContainer = hex("#3A3935"), onPrimaryContainer = hex("#D1B59A"),
    secondary = hex("#76B8D4"), onSecondary = hex("#21211F"),
    tertiary = hex("#7EC86C"), onTertiary = hex("#21211F"),
    background = hex("#21211F"), onBackground = hex("#D1B59A"),
    surface = hex("#2D2C29"), onSurface = hex("#D1B59A"),
    surfaceVariant = hex("#3A3935"), onSurfaceVariant = hex("#937B65"),
    error = hex("#E05252"), onError = Color.White,
    outline = hex("#524E48"),
)
private val EspressoLight = lightColorScheme(
    primary = hex("#8B6339"), onPrimary = Color.White,
    primaryContainer = hex("#EDE6D6"), onPrimaryContainer = hex("#3A2E1E"),
    secondary = hex("#1E40AF"), onSecondary = Color.White,
    tertiary = hex("#4D7C0F"), onTertiary = Color.White,
    background = hex("#FDF8F0"), onBackground = hex("#3A2E1E"),
    surface = hex("#FFFDF7"), onSurface = hex("#3A2E1E"),
    surfaceVariant = hex("#EDE6D6"), onSurfaceVariant = hex("#7A6A50"),
    error = hex("#B45309"), onError = Color.White,
    outline = hex("#D4C8B0"),
)

private val GazetteDark = darkColorScheme(
    primary = hex("#60A5FA"), onPrimary = hex("#0F1828"),
    primaryContainer = hex("#2A3650"), onPrimaryContainer = hex("#EAF2FF"),
    secondary = hex("#60A5FA"), onSecondary = hex("#0F1828"),
    tertiary = hex("#4ADE80"), onTertiary = hex("#0F1828"),
    background = hex("#1A2030"), onBackground = hex("#EAF2FF"),
    surface = hex("#222C3F"), onSurface = hex("#EAF2FF"),
    surfaceVariant = hex("#2A3650"), onSurfaceVariant = hex("#7A9CC0"),
    error = hex("#F87171"), onError = Color.White,
    outline = hex("#364766"),
)
private val GazetteLight = lightColorScheme(
    primary = hex("#3B82F6"), onPrimary = Color.White,
    primaryContainer = hex("#E4EEFF"), onPrimaryContainer = hex("#0A0A0A"),
    secondary = hex("#0284C7"), onSecondary = Color.White,
    tertiary = hex("#16A34A"), onTertiary = Color.White,
    background = hex("#F2F7FF"), onBackground = hex("#0A0A0A"),
    surface = hex("#FFFFFF"), onSurface = hex("#0A0A0A"),
    surfaceVariant = hex("#E4EEFF"), onSurfaceVariant = hex("#4A5568"),
    error = hex("#DC2626"), onError = Color.White,
    outline = hex("#C8D8F0"),
)

private val GraniteDark = darkColorScheme(
    primary = hex("#22A88E"), onPrimary = Color.White,
    primaryContainer = hex("#2F3B42"), onPrimaryContainer = hex("#F0F2F4"),
    secondary = hex("#60A5FA"), onSecondary = hex("#1D2327"),
    tertiary = hex("#4ADE80"), onTertiary = hex("#1D2327"),
    background = hex("#1D2327"), onBackground = hex("#F0F2F4"),
    surface = hex("#273035"), onSurface = hex("#F0F2F4"),
    surfaceVariant = hex("#2F3B42"), onSurfaceVariant = hex("#8EA4AE"),
    error = hex("#F87171"), onError = Color.White,
    outline = hex("#3A4A52"),
)
private val GraniteLight = lightColorScheme(
    primary = hex("#0F7A65"), onPrimary = Color.White,
    primaryContainer = hex("#D9EDEA"), onPrimaryContainer = hex("#142820"),
    secondary = hex("#0284C7"), onSecondary = Color.White,
    tertiary = hex("#16A34A"), onTertiary = Color.White,
    background = hex("#ECF2EF"), onBackground = hex("#142820"),
    surface = hex("#FFFFFF"), onSurface = hex("#142820"),
    surfaceVariant = hex("#D9EDEA"), onSurfaceVariant = hex("#3D6B60"),
    error = hex("#DC2626"), onError = Color.White,
    outline = hex("#B5D5CE"),
)

private val OneDarkDark = darkColorScheme(
    primary = hex("#98C379"), onPrimary = hex("#1E2227"),
    primaryContainer = hex("#3E4452"), onPrimaryContainer = hex("#DFD9D6"),
    secondary = hex("#61AFEF"), onSecondary = hex("#1E2227"),
    tertiary = hex("#98C379"), onTertiary = hex("#1E2227"),
    background = hex("#282C34"), onBackground = hex("#DFD9D6"),
    surface = hex("#31363F"), onSurface = hex("#DFD9D6"),
    surfaceVariant = hex("#3E4452"), onSurfaceVariant = hex("#9DA5B4"),
    error = hex("#E06C75"), onError = Color.White,
    outline = hex("#4B5263"),
)
private val OneDarkLight = lightColorScheme(
    primary = hex("#3A7A22"), onPrimary = Color.White,
    primaryContainer = hex("#E2EDD9"), onPrimaryContainer = hex("#1A2A15"),
    secondary = hex("#0284C7"), onSecondary = Color.White,
    tertiary = hex("#16A34A"), onTertiary = Color.White,
    background = hex("#F2F7EE"), onBackground = hex("#1A2A15"),
    surface = hex("#FFFFFF"), onSurface = hex("#1A2A15"),
    surfaceVariant = hex("#E2EDD9"), onSurfaceVariant = hex("#4A6840"),
    error = hex("#DC2626"), onError = Color.White,
    outline = hex("#C4D9B8"),
)

private val PaperDark = darkColorScheme(
    primary = hex("#C4A97A"), onPrimary = hex("#1E1C18"),
    primaryContainer = hex("#353028"), onPrimaryContainer = hex("#E8D9C0"),
    secondary = hex("#76B8D4"), onSecondary = hex("#1E1C18"),
    tertiary = hex("#7EC86C"), onTertiary = hex("#1E1C18"),
    background = hex("#1E1C18"), onBackground = hex("#E8D9C0"),
    surface = hex("#2A2822"), onSurface = hex("#E8D9C0"),
    surfaceVariant = hex("#353028"), onSurfaceVariant = hex("#9A8B72"),
    error = hex("#E05252"), onError = Color.White,
    outline = hex("#4A4438"),
)
private val PaperLight = lightColorScheme(
    primary = hex("#AA9A73"), onPrimary = Color.White,
    primaryContainer = hex("#EDE9DF"), onPrimaryContainer = hex("#4C432E"),
    secondary = hex("#1E40AF"), onSecondary = Color.White,
    tertiary = hex("#4D7C0F"), onTertiary = Color.White,
    background = hex("#F8F6F1"), onBackground = hex("#4C432E"),
    surface = hex("#FFFFF8"), onSurface = hex("#4C432E"),
    surfaceVariant = hex("#EDE9DF"), onSurfaceVariant = hex("#7A6E58"),
    error = hex("#B45309"), onError = Color.White,
    outline = hex("#D6CDB8"),
)

private val PassionDark = darkColorScheme(
    primary = hex("#CE93D8"), onPrimary = hex("#1A0A2E"),
    primaryContainer = hex("#301655"), onPrimaryContainer = hex("#EDE0F8"),
    secondary = hex("#90CAF9"), onSecondary = hex("#1A0A2E"),
    tertiary = hex("#A5D6A7"), onTertiary = hex("#1A0A2E"),
    background = hex("#1A0A2E"), onBackground = hex("#EDE0F8"),
    surface = hex("#251040"), onSurface = hex("#EDE0F8"),
    surfaceVariant = hex("#301655"), onSurfaceVariant = hex("#9B71C0"),
    error = hex("#F48FB1"), onError = hex("#1A0A2E"),
    outline = hex("#4A2575"),
)
private val PassionLight = lightColorScheme(
    primary = hex("#8E24AA"), onPrimary = Color.White,
    primaryContainer = hex("#EDE7F6"), onPrimaryContainer = hex("#12005E"),
    secondary = hex("#0277BD"), onSecondary = Color.White,
    tertiary = hex("#2E7D32"), onTertiary = Color.White,
    background = hex("#F5F5F5"), onBackground = hex("#12005E"),
    surface = hex("#FFFFFF"), onSurface = hex("#12005E"),
    surfaceVariant = hex("#EDE7F6"), onSurfaceVariant = hex("#4527A0"),
    error = hex("#C62828"), onError = Color.White,
    outline = hex("#D1C4E9"),
)

private val TangibleDark = darkColorScheme(
    primary = hex("#A78BFA"), onPrimary = hex("#1A1D29"),
    primaryContainer = hex("#2C3150"), onPrimaryContainer = hex("#EDEDFC"),
    secondary = hex("#60A5FA"), onSecondary = hex("#1A1D29"),
    tertiary = hex("#4ADE80"), onTertiary = hex("#1A1D29"),
    background = hex("#1A1D29"), onBackground = hex("#EDEDFC"),
    surface = hex("#222637"), onSurface = hex("#EDEDFC"),
    surfaceVariant = hex("#2C3150"), onSurfaceVariant = hex("#9090BB"),
    error = hex("#F87171"), onError = Color.White,
    outline = hex("#3B4172"),
)
private val TangibleLight = lightColorScheme(
    primary = hex("#7C3AED"), onPrimary = Color.White,
    primaryContainer = hex("#EEECFF"), onPrimaryContainer = hex("#1A1D29"),
    secondary = hex("#0369A1"), onSecondary = Color.White,
    tertiary = hex("#16A34A"), onTertiary = Color.White,
    background = hex("#F7F6FF"), onBackground = hex("#1A1D29"),
    surface = hex("#FFFFFF"), onSurface = hex("#1A1D29"),
    surfaceVariant = hex("#EEECFF"), onSurfaceVariant = hex("#5C5C80"),
    error = hex("#DC2626"), onError = Color.White,
    outline = hex("#D4D0F0"),
)

private val TronDark = darkColorScheme(
    primary = hex("#6EE2FF"), onPrimary = hex("#1A2530"),
    primaryContainer = hex("#3A4554"), onPrimaryContainer = hex("#EFFBFF"),
    secondary = hex("#6EE2FF"), onSecondary = hex("#1A2530"),
    tertiary = hex("#51FA7B"), onTertiary = hex("#1A2530"),
    background = hex("#242B33"), onBackground = hex("#EFFBFF"),
    surface = hex("#2E3742"), onSurface = hex("#EFFBFF"),
    surfaceVariant = hex("#3A4554"), onSurfaceVariant = hex("#8DBDCC"),
    error = hex("#FF6B6B"), onError = Color.White,
    outline = hex("#4A5A6A"),
)
private val TronLight = lightColorScheme(
    primary = hex("#0891B2"), onPrimary = Color.White,
    primaryContainer = hex("#D0EFFB"), onPrimaryContainer = hex("#071820"),
    secondary = hex("#0891B2"), onSecondary = Color.White,
    tertiary = hex("#16A34A"), onTertiary = Color.White,
    background = hex("#EAF8FD"), onBackground = hex("#071820"),
    surface = hex("#FFFFFF"), onSurface = hex("#071820"),
    surfaceVariant = hex("#D0EFFB"), onSurfaceVariant = hex("#2E6880"),
    error = hex("#DC2626"), onError = Color.White,
    outline = hex("#A0D8F0"),
)

// ── Scheme lookup ─────────────────────────────────────────────────────────────
private fun colorScheme(paletteId: String, dark: Boolean) = when (paletteId) {
    "blackboard" -> if (dark) BlackboardDark else BlackboardLight
    "blues"      -> if (dark) BluesDark      else BluesLight
    "cloud"      -> if (dark) CloudDark      else CloudLight
    "espresso"   -> if (dark) EspressoDark   else EspressoLight
    "gazette"    -> if (dark) GazetteDark    else GazetteLight
    "onedark"    -> if (dark) OneDarkDark    else OneDarkLight
    "paper"      -> if (dark) PaperDark      else PaperLight
    "passion"    -> if (dark) PassionDark    else PassionLight
    "tangible"   -> if (dark) TangibleDark   else TangibleLight
    "tron"       -> if (dark) TronDark       else TronLight
    else         -> if (dark) GraniteDark    else GraniteLight  // "granite" + fallback
}

// ── Theme ─────────────────────────────────────────────────────────────────────
@Composable
fun TangibleTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    paletteId: String = DEFAULT_PALETTE_ID,
    content: @Composable () -> Unit,
) {
    MaterialTheme(
        colorScheme = colorScheme(paletteId, darkTheme),
        content = content,
    )
}
