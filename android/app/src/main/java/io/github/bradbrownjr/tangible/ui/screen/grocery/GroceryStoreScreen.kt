package io.github.bradbrownjr.tangible.ui.screen.grocery

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.Edit
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import io.github.bradbrownjr.tangible.data.remote.GroceryAisleDto
import io.github.bradbrownjr.tangible.data.remote.GroceryStoreDto
import io.github.bradbrownjr.tangible.data.repo.GroceryRepository
import javax.inject.Inject

private data class GroceryCategoryPreset(val slug: String, val label: String)

private val GROCERY_CATEGORY_PRESETS = listOf(
    GroceryCategoryPreset("produce",             "Produce"),
    GroceryCategoryPreset("bread",               "Bread"),
    GroceryCategoryPreset("bakery",              "Bakery"),
    GroceryCategoryPreset("meat-seafood",        "Meat & Seafood"),
    GroceryCategoryPreset("deli",                "Deli"),
    GroceryCategoryPreset("dairy-eggs",          "Dairy & Eggs"),
    GroceryCategoryPreset("frozen",              "Frozen"),
    GroceryCategoryPreset("canned-pantry",       "Canned & Pantry"),
    GroceryCategoryPreset("pasta-grains",        "Pasta & Grains"),
    GroceryCategoryPreset("snacks",              "Snacks"),
    GroceryCategoryPreset("beverages",           "Beverages"),
    GroceryCategoryPreset("breakfast-cereal",    "Breakfast & Cereal"),
    GroceryCategoryPreset("condiments-spices",   "Condiments & Spices"),
    GroceryCategoryPreset("cleaning-household",  "Cleaning & Household"),
    GroceryCategoryPreset("health-beauty",       "Health & Beauty"),
    GroceryCategoryPreset("pet-supplies",        "Pet Supplies"),
    GroceryCategoryPreset("alcohol",             "Alcohol"),
)

private val PRESET_SLUGS = GROCERY_CATEGORY_PRESETS.map { it.slug }.toSet()

data class GroceryStoreListUi(
    val stores: List<GroceryStoreDto> = emptyList(),
    val loading: Boolean = false,
    val error: String? = null,
)

@HiltViewModel
class GroceryStoreListViewModel @Inject constructor(
    private val groceryRepo: GroceryRepository,
) : ViewModel() {
    private val _state = MutableStateFlow(GroceryStoreListUi())
    val state: StateFlow<GroceryStoreListUi> = _state.asStateFlow()

    init { load() }

    fun load() {
        _state.value = _state.value.copy(loading = true, error = null)
        viewModelScope.launch {
            try {
                val stores = groceryRepo.listStores()
                _state.value = _state.value.copy(stores = stores, loading = false)
            } catch (t: Throwable) {
                _state.value = _state.value.copy(loading = false, error = t.message)
            }
        }
    }

    fun createStore(name: String) {
        viewModelScope.launch {
            try {
                groceryRepo.createStore(name)
                load()
            } catch (t: Throwable) {
                _state.value = _state.value.copy(error = t.message)
            }
        }
    }

    fun deleteStore(id: String) {
        viewModelScope.launch {
            try {
                groceryRepo.deleteStore(id)
                _state.value = _state.value.copy(stores = _state.value.stores.filter { it.id != id })
            } catch (t: Throwable) {
                _state.value = _state.value.copy(error = t.message)
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun GroceryStoreListScreen(
    viewModel: GroceryStoreListViewModel = hiltViewModel(),
    onBack: () -> Unit,
    onOpenStore: (storeId: String) -> Unit,
) {
    val ui by viewModel.state.collectAsState()
    var showCreateDialog by remember { mutableStateOf(false) }
    var confirmDeleteStore by remember { mutableStateOf<GroceryStoreDto?>(null) }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("My Stores") },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
                    }
                },
            )
        },
        floatingActionButton = {
            FloatingActionButton(onClick = { showCreateDialog = true }) {
                Icon(Icons.Default.Add, contentDescription = "Add store")
            }
        },
    ) { innerPadding ->
        Box(modifier = Modifier.fillMaxSize().padding(innerPadding)) {
            when {
                ui.loading -> {
                    CircularProgressIndicator(modifier = Modifier.align(Alignment.Center))
                }
                ui.stores.isEmpty() && !ui.loading -> {
                    Column(
                        modifier = Modifier.align(Alignment.Center),
                        horizontalAlignment = Alignment.CenterHorizontally,
                        verticalArrangement = Arrangement.spacedBy(8.dp),
                    ) {
                        Text("No stores yet.", style = MaterialTheme.typography.bodyLarge)
                        Text(
                            "Add a store to sort your shopping list by aisle.",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                    }
                }
                else -> {
                    LazyColumn(contentPadding = PaddingValues(vertical = 8.dp)) {
                        items(ui.stores, key = { it.id }) { store ->
                            ListItem(
                                headlineContent = { Text(store.name) },
                                supportingContent = {
                                    Text("${store.aisles.size} aisle${if (store.aisles.size == 1) "" else "s"}")
                                },
                                trailingContent = {
                                    Row {
                                        IconButton(onClick = { onOpenStore(store.id) }) {
                                            Icon(Icons.Default.Edit, contentDescription = "Edit aisles")
                                        }
                                        IconButton(onClick = { confirmDeleteStore = store }) {
                                            Icon(
                                                Icons.Default.Delete,
                                                contentDescription = "Delete store",
                                                tint = MaterialTheme.colorScheme.error,
                                            )
                                        }
                                    }
                                },
                                modifier = Modifier.clickable { onOpenStore(store.id) },
                            )
                            HorizontalDivider()
                        }
                    }
                }
            }
            if (ui.error != null) {
                Snackbar(modifier = Modifier.align(Alignment.BottomCenter).padding(16.dp)) {
                    Text(ui.error!!)
                }
            }
        }
    }

    if (showCreateDialog) {
        NameInputDialog(
            title = "New store",
            label = "Store name",
            onDismiss = { showCreateDialog = false },
            onConfirm = { name -> viewModel.createStore(name); showCreateDialog = false },
        )
    }

    confirmDeleteStore?.let { store ->
        AlertDialog(
            onDismissRequest = { confirmDeleteStore = null },
            title = { Text("Delete store?") },
            text = { Text("\"${store.name}\" and all its aisles will be deleted. Your grocery list is not affected.") },
            confirmButton = {
                Button(
                    onClick = { viewModel.deleteStore(store.id); confirmDeleteStore = null },
                    colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.error),
                ) { Text("Delete") }
            },
            dismissButton = { TextButton(onClick = { confirmDeleteStore = null }) { Text("Cancel") } },
        )
    }
}

// ---------------------------------------------------------------------------
// Aisle editor screen
// ---------------------------------------------------------------------------

data class GroceryAisleEditorUi(
    val store: GroceryStoreDto? = null,
    val loading: Boolean = false,
    val error: String? = null,
)

@HiltViewModel
class GroceryAisleEditorViewModel @Inject constructor(
    private val groceryRepo: GroceryRepository,
    savedState: SavedStateHandle,
) : ViewModel() {
    private val storeId: String = checkNotNull(savedState["storeId"])
    private val _state = MutableStateFlow(GroceryAisleEditorUi())
    val state: StateFlow<GroceryAisleEditorUi> = _state.asStateFlow()

    init { load() }

    fun load() {
        _state.value = _state.value.copy(loading = true, error = null)
        viewModelScope.launch {
            try {
                val stores = groceryRepo.listStores()
                _state.value = _state.value.copy(
                    store = stores.find { it.id == storeId },
                    loading = false,
                )
            } catch (t: Throwable) {
                _state.value = _state.value.copy(loading = false, error = t.message)
            }
        }
    }

    fun createAisle(name: String, categorySlugs: List<String>) {
        viewModelScope.launch {
            try {
                val position = (_state.value.store?.aisles?.maxOfOrNull { it.position } ?: -1) + 1
                groceryRepo.createAisle(storeId, name, position, categorySlugs)
                load()
            } catch (t: Throwable) {
                _state.value = _state.value.copy(error = t.message)
            }
        }
    }

    fun updateAisle(aisleId: String, name: String, categorySlugs: List<String>) {
        viewModelScope.launch {
            try {
                groceryRepo.updateAisle(storeId, aisleId, name = name, categorySlugs = categorySlugs)
                load()
            } catch (t: Throwable) {
                _state.value = _state.value.copy(error = t.message)
            }
        }
    }

    fun deleteAisle(aisleId: String) {
        viewModelScope.launch {
            try {
                groceryRepo.deleteAisle(storeId, aisleId)
                _state.value = _state.value.copy(
                    store = _state.value.store?.copy(
                        aisles = _state.value.store!!.aisles.filter { it.id != aisleId }
                    )
                )
            } catch (t: Throwable) {
                _state.value = _state.value.copy(error = t.message)
            }
        }
    }

    fun moveAisleUp(aisleId: String) {
        val aisles = _state.value.store?.aisles?.sortedBy { it.position } ?: return
        val idx = aisles.indexOfFirst { it.id == aisleId }.takeIf { it > 0 } ?: return
        val reordered = aisles.toMutableList().also { list ->
            val tmp = list[idx]; list[idx] = list[idx - 1]; list[idx - 1] = tmp
        }
        viewModelScope.launch {
            try {
                groceryRepo.reorderAisles(storeId, reordered.map { it.id })
                load()
            } catch (t: Throwable) {
                _state.value = _state.value.copy(error = t.message)
            }
        }
    }

    fun moveAisleDown(aisleId: String) {
        val aisles = _state.value.store?.aisles?.sortedBy { it.position } ?: return
        val idx = aisles.indexOfFirst { it.id == aisleId }.takeIf { it < aisles.lastIndex } ?: return
        val reordered = aisles.toMutableList().also { list ->
            val tmp = list[idx]; list[idx] = list[idx + 1]; list[idx + 1] = tmp
        }
        viewModelScope.launch {
            try {
                groceryRepo.reorderAisles(storeId, reordered.map { it.id })
                load()
            } catch (t: Throwable) {
                _state.value = _state.value.copy(error = t.message)
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun GroceryAisleEditorScreen(
    viewModel: GroceryAisleEditorViewModel = hiltViewModel(),
    onBack: () -> Unit,
) {
    val ui by viewModel.state.collectAsState()
    var showCreateDialog by remember { mutableStateOf(false) }
    var editAisle by remember { mutableStateOf<GroceryAisleDto?>(null) }
    var confirmDeleteAisle by remember { mutableStateOf<GroceryAisleDto?>(null) }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(ui.store?.name ?: "Aisles") },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
                    }
                },
            )
        },
        floatingActionButton = {
            FloatingActionButton(onClick = { showCreateDialog = true }) {
                Icon(Icons.Default.Add, contentDescription = "Add aisle")
            }
        },
    ) { innerPadding ->
        Box(modifier = Modifier.fillMaxSize().padding(innerPadding)) {
            when {
                ui.loading -> CircularProgressIndicator(modifier = Modifier.align(Alignment.Center))
                else -> {
                    val aisles = ui.store?.aisles?.sortedBy { it.position } ?: emptyList()
                    if (aisles.isEmpty()) {
                        Column(
                            modifier = Modifier.align(Alignment.Center).padding(16.dp),
                            horizontalAlignment = Alignment.CenterHorizontally,
                            verticalArrangement = Arrangement.spacedBy(8.dp),
                        ) {
                            Text("No aisles yet.", style = MaterialTheme.typography.bodyLarge)
                            Text(
                                "Add aisles and assign category slugs to each one.\n" +
                                    "Your grocery list will then be sorted by aisle order.",
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant,
                            )
                        }
                    } else {
                        LazyColumn(contentPadding = PaddingValues(vertical = 8.dp)) {
                            itemsIndexed(aisles, key = { _, a -> a.id }) { idx, aisle ->
                                ListItem(
                                    headlineContent = { Text(aisle.name) },
                                    supportingContent = {
                                        if (aisle.category_slugs.isNotEmpty()) {
                                            Text(aisle.category_slugs.joinToString(", "))
                                        }
                                    },
                                    overlineContent = { Text("Position ${idx + 1}") },
                                    trailingContent = {
                                        Row {
                                            IconButton(onClick = { editAisle = aisle }) {
                                                Icon(Icons.Default.Edit, contentDescription = "Edit")
                                            }
                                            IconButton(onClick = { confirmDeleteAisle = aisle }) {
                                                Icon(
                                                    Icons.Default.Delete,
                                                    contentDescription = "Delete",
                                                    tint = MaterialTheme.colorScheme.error,
                                                )
                                            }
                                        }
                                    },
                                    modifier = Modifier.clickable { editAisle = aisle },
                                )
                                HorizontalDivider()
                            }
                        }
                    }
                }
            }
            if (ui.error != null) {
                Snackbar(modifier = Modifier.align(Alignment.BottomCenter).padding(16.dp)) {
                    Text(ui.error!!)
                }
            }
        }
    }

    if (showCreateDialog) {
        AisleInputDialog(
            title = "New aisle",
            initialName = "",
            initialSlugs = emptyList(),
            onDismiss = { showCreateDialog = false },
            onConfirm = { name, slugs ->
                viewModel.createAisle(name, slugs)
                showCreateDialog = false
            },
        )
    }

    editAisle?.let { aisle ->
        AisleInputDialog(
            title = "Edit aisle",
            initialName = aisle.name,
            initialSlugs = aisle.category_slugs,
            onDismiss = { editAisle = null },
            onConfirm = { name, slugs ->
                viewModel.updateAisle(aisle.id, name, slugs)
                editAisle = null
            },
        )
    }

    confirmDeleteAisle?.let { aisle ->
        AlertDialog(
            onDismissRequest = { confirmDeleteAisle = null },
            title = { Text("Delete aisle?") },
            text = { Text("\"${aisle.name}\" will be removed from this store.") },
            confirmButton = {
                Button(
                    onClick = { viewModel.deleteAisle(aisle.id); confirmDeleteAisle = null },
                    colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.error),
                ) { Text("Delete") }
            },
            dismissButton = { TextButton(onClick = { confirmDeleteAisle = null }) { Text("Cancel") } },
        )
    }
}

private fun String.parseSlugs(): List<String> =
    split(",", "\n").map { it.trim() }.filter { it.isNotBlank() }

// ---------------------------------------------------------------------------
// Shared dialogs
// ---------------------------------------------------------------------------

@Composable
private fun NameInputDialog(
    title: String,
    label: String,
    initialValue: String = "",
    onDismiss: () -> Unit,
    onConfirm: (String) -> Unit,
) {
    var value by remember { mutableStateOf(initialValue) }
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(title) },
        text = {
            OutlinedTextField(
                value = value,
                onValueChange = { value = it },
                label = { Text(label) },
                singleLine = true,
                modifier = Modifier.fillMaxWidth(),
            )
        },
        confirmButton = {
            Button(onClick = { if (value.isNotBlank()) onConfirm(value.trim()) }, enabled = value.isNotBlank()) {
                Text("Save")
            }
        },
        dismissButton = { TextButton(onClick = onDismiss) { Text("Cancel") } },
    )
}

@OptIn(ExperimentalLayoutApi::class)
@Composable
private fun AisleInputDialog(
    title: String,
    initialName: String,
    initialSlugs: List<String>,
    onDismiss: () -> Unit,
    onConfirm: (name: String, slugs: List<String>) -> Unit,
) {
    var name by remember { mutableStateOf(initialName) }
    val selectedSlugs = remember {
        mutableStateOf(initialSlugs.filter { it in PRESET_SLUGS }.toSet())
    }
    var customText by remember {
        mutableStateOf(
            initialSlugs.filter { it !in PRESET_SLUGS }.joinToString(", ")
        )
    }

    fun buildSlugs(): List<String> {
        val result = selectedSlugs.value.toMutableList()
        customText.split(",").map { it.trim().lowercase().replace(" ", "-") }
            .filter { it.isNotBlank() && it !in result }
            .forEach { result.add(it) }
        return result
    }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(title) },
        text = {
            Column(
                modifier = Modifier.verticalScroll(rememberScrollState()),
                verticalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                OutlinedTextField(
                    value = name,
                    onValueChange = { name = it },
                    label = { Text("Aisle name *") },
                    placeholder = { Text("e.g. Dairy, Produce, Aisle 3") },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth(),
                )
                Text("Categories", style = MaterialTheme.typography.labelMedium)
                FlowRow(
                    horizontalArrangement = Arrangement.spacedBy(6.dp),
                    verticalArrangement = Arrangement.spacedBy(6.dp),
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    GROCERY_CATEGORY_PRESETS.forEach { cat ->
                        FilterChip(
                            selected = cat.slug in selectedSlugs.value,
                            onClick = {
                                selectedSlugs.value = if (cat.slug in selectedSlugs.value)
                                    selectedSlugs.value - cat.slug
                                else
                                    selectedSlugs.value + cat.slug
                            },
                            label = { Text(cat.label) },
                        )
                    }
                }
                OutlinedTextField(
                    value = customText,
                    onValueChange = { customText = it },
                    label = { Text("Custom categories (optional)") },
                    placeholder = { Text("e.g. organic, gluten-free") },
                    supportingText = { Text("Comma-separated. Items with matching categories appear in this aisle.") },
                    maxLines = 3,
                    modifier = Modifier.fillMaxWidth(),
                )
            }
        },
        confirmButton = {
            Button(
                onClick = { if (name.isNotBlank()) onConfirm(name.trim(), buildSlugs()) },
                enabled = name.isNotBlank(),
            ) { Text("Save") }
        },
        dismissButton = { TextButton(onClick = onDismiss) { Text("Cancel") } },
    )
}
