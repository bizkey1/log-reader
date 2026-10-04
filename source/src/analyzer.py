
import re
from pathlib import Path

REGLAS = {
    "CRASH": r"Preparing crash report(?: with UUID)?|Saving crash report to|Saving crash report|Generating crash report|Crash report saved(?: to)?|This crash report has been saved to|---- Minecraft Crash Report ----|#@!@#\s*Game crashed!?(?:\s+Crash report saved to:)?|#@!@#\s*Server crashed!?(?:\s+Crash report saved to:)?",
    "WATCHDOG": r"single server tick has taken .*milliseconds|server watchdog|IntegratedWatchdog|The server has stopped responding",
    "DEPENDENCIA_REQUERIDA": r"missing required dependency|missing dependency|requires .*?(?:version|mod)|depends on .*?(?:version|mod)|requires .* to be installed|mandatory dependency",
    "DEPENDENCIA_RECOMENDADA": r"recommends .*?(?:version|mod)|optional dependency|recommended dependency",
    "MOD_LOAD_ERROR": r"Failed to load mod|Loading errors encountered|Error loading mod|ModLoadingException|failed to load .* mod|mod .* could not be loaded",
    "INVALID_MOD": r"Invalid mod file|Failed to load mod file|Could not find required mod|missing or invalid mod|not a valid mod",
    "DUPLICATE_MOD": r"Duplicate mods|duplicate mod|more than one copy of mod|Found duplicate",
    "VERSION_INCOMPATIBLE": r"incompatible with.*(?:minecraft|loader|forge|fabric|neoforge)|requires minecraft .* but|requires .* loader|only supports minecraft|not compatible with the current|version differences that were not resolved",
    "CLASS_NOT_FOUND": r"ClassNotFoundException|NoClassDefFoundError|Error loading class|Could not load class|Could not find parent",
    "EXCEPTION": r"\b[A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)*(?:Exception|Error)\b",
    "EXPRESSION_ERROR": r"Couldn't parse an expression|Failed to parse an expression|most likely something wrong in the MoLang",
    "EVENT_HANDLER_ERROR": r"An error occurred building event handler|Failed to build event handler",
    "MIXIN_CONFLICT": r"Redirect conflict|already redirected by|Static binding violation|Method overwrite conflict|Overwrite.*conflict|Injection.*failed|Mixin.*failed|Mod mixin into .* detected",
    "MIXIN_NOT_FOUND": r"Mixin.*not found|Could not find.*mixin|target.*mixin.*not found|No targets matched",
    "MIXIN_DISABLED": r"Force-disabling.*mixin|Mixin.*disabled|Cancelled mixin",
    "MIXIN_ENABLED": r"Force-enabling.*mixin|enables it$",
    "REGISTRY_ERROR": r"Registry .* was empty|Failed to register|Failed to load registries|Registry.*error|registry.*failed|Hanging sign material .* was null|defineId called for|Unidentified mapping from registry|detected missing registry entries|There are unidentified mappings|Registry entry .* was not realized",
    "RECIPE_ERROR": r"Exception thrown registering.*\brecipes?\b|Error.*\brecipes?\b|Failed to parse \brecipes?\b|Couldn't parse \brecipes?\b",
    "ADVANCEMENT_ERROR": r"Error.*advancement|Exception.*advancement|Failed to parse advancement",
    "LOOT_DATA_ERROR": r"Couldn't parse element .*loot_table|Failed to parse either.*Unknown registry key|Unknown registry key.*loot|loot table",
    "TAG_MISSING": r"Not all defined tags .* are present|Missing required tags|Couldn't load tag",
    "UNKNOWN_BLOCK": r"Unknown block|Unknown blockstate property|Unable to read property|Unknown block entity",
    "MISSING_SOUND": r"Missing sound for|Unable to play empty soundEvent|Unable to play sound|Unable to load sound|does not exist, cannot add it to event",
    "MISSING_MODEL": r"Unable to load model|Missing model|Unable to bake model|Failed to generate model",
    "MISSING_TEXTURE": r"Missing texture|Missing textures|Texture .* not found",
    "SHADER": r"could not find (?:uniform|sampler)|failed to find (?:uniform|sampler)|cannot find (?:uniform|sampler)|missing (?:uniform|sampler)",
    "RESOURCEPACK_INCOMPATIBLE": r"resource pack .* not compatible|Temporarily disabling .* batching|Temporarily disabling font atlas",
    "FANCYMENU": r"\[FANCYMENU\]",
    "GL_ERROR": r"GL ERROR|Invalid scancode|OpenGL error|GL_INVALID_",
    "SOUND_ENGINE": r"Sound engine.*ERROR|OpenAL error|AL_INVALID_",
    "SERVER_LAG": r"Can't keep up!|Running \d+(?:\.\d+)?ms or \d+ ticks behind|Server seems overloading",
    "MOVEMENT": r"moved too quickly!",
    "ENTITY_NOT_FOUND": r"Entity .* wasn't found in section|wasn't found in section .*DISCARDED",
    "ENTITY_ATTRIBUTE_ERROR": r"Entity .* has no attributes|model attempted creation more than 64 times",
    "NETWORK_TIMEOUT": r"timed out|timeout|Connection reset|Connection refused|Disconnected from server|Read timed out|Network Exception Caught|Unknown custom packet identifier",
    "VERSION_FORMAT": r"isn't compatible with Loader's extended semantic version format|Could not parse version number component",
    "CONFIG_REFERENCE": r"Config issue on line|does not exist, ignoring rule|Unknown config|invalid config|Unknown preset name",
    "CONFIG_DEFAULT_VALUE": r"Incorrect key .* was corrected from .* to its default|was corrected from null to its default|default value",
    "MOD_METADATA": r"missing mods\.toml|mods\.toml file|missing fabric.mod.json|fabric\.mod\.json.*missing",
    "RESOURCEPACK_WORKAROUND": r"PathResourcePack base class instantiated|should be calling ResourcePackLoader\.createPackForMod|Applying workaround",
    "MISSING_DATAPACK_MOD": r"Missing data pack mod:|Missing data pack ",
    "REGISTRY_ID_MISMATCH": r"Object did not get ID it asked for|Expected:\s*\d+\s+Got:\s*\d+",
    "MIXIN_CONFIG_WARNING": r"Mixin config .* does not specify .*minVersion|does not specify \"minVersion\"",
    "CONFIG_OVERWRITE": r"Overwriting non-null config",
    "REFERENCE_MAP": r"Reference map .* could not be read|refmap.*could not be read",
    "OS_INCOMPATIBLE": r"not compatible with your operating system|Unsupported operating system|OS mismatch|only applies to OS:",
    "WORLD_DATA": r"Did not find a region folder for level:",
    "NON_FABRIC_MOD": r"Found \d+ non-fabric mod|non-fabric mod",
    "OPTION_OVERRIDE": r"attempted to override option|option .* overriden|option .* overridden",
    "DUPLICATE_UUID": r"UUID of added entity already exists|Duplicate UUID",
    "REGISTRY_VALUE_TYPE": r"Invalid registry value type detected",
    "LOAD_TIME": r"took \d+(?:\.\d+)? seconds to load|total game/world load|Game took \d+(?:\.\d+)?|Time from main menu to in-game was|Total time to load game and open world was|Datapack reload took|took \d+(?:\.\d+)? s to run a deferred task",
    "BROKEN_API": r"broken implementation of .*Api|broken implementation",
    "LEGACY_MODE": r"loaded in legacy mode|legacy mode",
    "RESOURCE_FORMAT": r"improper file name format|should end in \.animation\.json|Invalid path in datapack|unsupported geometry json version|ignored non-lowercase namespace",
    "TEXTURE_SIZE": r"limits mip level|dropping miplevel",
    "PACK_FORMAT": r"declared support for versions .* defaulting to",
    "PARTIAL_INCOMPATIBILITY": r"Partially Incompatible .* mod detected|Partially Incompatible|might not work well due to .* bug",
    "GC_WARNING": r"Garbage collector detected",
    "NO_DATA_FIXER": r"No data fixer registered",
}

TYPE_LABELS = {
    "CRASH": "Crash",
    "WATCHDOG": "Server Watchdog",
    "DEPENDENCIA_REQUERIDA": "Required Dependency",
    "DEPENDENCIA_RECOMENDADA": "Recommended Dependency",
    "MOD_LOAD_ERROR": "Mod Loading Error",
    "INVALID_MOD": "Invalid Mod",
    "DUPLICATE_MOD": "Duplicate Mod",
    "VERSION_INCOMPATIBLE": "Version Incompatibility",
    "CLASS_NOT_FOUND": "Class Not Found",
    "EXCEPTION": "Exception",
    "MIXIN_CONFLICT": "Mixin Conflict",
    "MIXIN_NOT_FOUND": "Mixin Target Not Found",
    "MIXIN_DISABLED": "Mixin Disabled",
    "MIXIN_ENABLED": "Mixin Force-Enabled",
    "REGISTRY_ERROR": "Registry Error",
    "RECIPE_ERROR": "Recipe Error",
    "ADVANCEMENT_ERROR": "Advancement Error",
    "LOOT_DATA_ERROR": "Loot Data Error",
    "TAG_MISSING": "Missing Tag",
    "UNKNOWN_BLOCK": "Unknown Block",
    "MISSING_SOUND": "Missing Sound",
    "MISSING_MODEL": "Missing Model",
    "MISSING_TEXTURE": "Missing Texture",
    "SHADER": "Shader Error",
    "RESOURCEPACK_INCOMPATIBLE": "Resource Pack Incompatibility",
    "FANCYMENU": "FancyMenu Error",
    "GL_ERROR": "OpenGL/GLFW Error",
    "SOUND_ENGINE": "Sound Engine Error",
    "SERVER_LAG": "Server Lag",
    "MOVEMENT": "Movement Warning",
    "ENTITY_NOT_FOUND": "Entity Not Found",
    "ENTITY_ATTRIBUTE_ERROR": "Entity Attribute Error",
    "NETWORK_TIMEOUT": "Network Timeout",
    "VERSION_FORMAT": "Version Format Warning",
    "CONFIG_REFERENCE": "Configuration Reference",
    "CONFIG_DEFAULT_VALUE": "Configuration Default Value",
    "MOD_METADATA": "Mod Metadata Warning",
    "RESOURCEPACK_WORKAROUND": "Resource Pack Workaround",
    "MISSING_DATAPACK_MOD": "Missing Data Pack Mod",
    "REGISTRY_ID_MISMATCH": "Registry ID Mismatch",
    "MIXIN_CONFIG_WARNING": "Mixin Configuration Warning",
    "CONFIG_OVERWRITE": "Configuration Overwrite",
    "REFERENCE_MAP": "Reference Map Error",
    "OS_INCOMPATIBLE": "Operating System Incompatibility",
    "WORLD_DATA": "World Data Warning",
    "NON_FABRIC_MOD": "Non-Fabric Mod",
    "OPTION_OVERRIDE": "Option Override",
    "DUPLICATE_UUID": "Duplicate Entity UUID",
    "REGISTRY_VALUE_TYPE": "Registry Value Type Error",
    "LOAD_TIME": "Long Load Time",
    "BROKEN_API": "Broken API",
    "LEGACY_MODE": "Legacy Mode",
    "RESOURCE_FORMAT": "Resource Format Warning",
    "TEXTURE_SIZE": "Texture Size Warning",
    "PACK_FORMAT": "Pack Format Warning",
    "PARTIAL_INCOMPATIBILITY": "Partial Incompatibility",
    "GC_WARNING": "Garbage Collector Warning",
    "NO_DATA_FIXER": "Missing Data Fixer",
    "EXPRESSION_ERROR": "Expression Parsing Error",
    "EVENT_HANDLER_ERROR": "Event Handler Error",
    "OTRO": "Other",
}


SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}

WHY_THIS_MATTERS = {
    "CRASH": "Minecraft generated a crash report, so the session or server process did not complete normally.",
    "WATCHDOG": "A server tick exceeded the watchdog threshold. This can freeze a server and may lead to a watchdog shutdown.",
    "DEPENDENCIA_REQUERIDA": "A required dependency is missing or incompatible. The affected mod may fail to load or function correctly.",
    "MOD_LOAD_ERROR": "A mod failed during loading or initialization, which can prevent startup or disable that mod's features.",
    "INVALID_MOD": "The loader could not accept the mod file, so its contents may not be available to the game.",
    "DUPLICATE_MOD": "Multiple copies of a mod can cause ambiguous loading and version conflicts.",
    "VERSION_INCOMPATIBLE": "The log reports a version mismatch between components that are expected to work together.",
    "CLASS_NOT_FOUND": "A required class is unavailable. This often points to a missing dependency or incompatible component version.",
    "MIXIN_CONFLICT": "A code injection could not be applied. Depending on the target, this can break a mod feature or startup.",
    "MIXIN_NOT_FOUND": "A mixin target is missing from the loaded environment, usually indicating a version or compatibility mismatch.",
    "REGISTRY_ERROR": "Registry content could not be registered or resolved, which can affect blocks, items, entities, or other game content.",
    "RECIPE_ERROR": "A recipe could not be parsed or registered, so that recipe may be unavailable.",
    "ADVANCEMENT_ERROR": "An advancement could not be parsed or registered, so related progression content may be unavailable.",
    "LOOT_DATA_ERROR": "A loot resource could not be resolved, potentially affecting drops or loot-table driven content.",
    "TAG_MISSING": "Required tags are missing, so recipes, data packs, or mod content that depends on them may behave incorrectly.",
    "NETWORK_TIMEOUT": "A connection or network operation timed out or was reset, which can interrupt multiplayer or resource loading.",
    "SERVER_LAG": "The server is processing ticks late. Repeated delays can cause rubber-banding, timeouts, or watchdog failures.",
    "GL_ERROR": "The graphics layer reported an OpenGL/GLFW problem that can affect rendering or input.",
    "SOUND_ENGINE": "The audio subsystem reported an error. This usually affects sound playback rather than core game logic.",
    "MISSING_TEXTURE": "A texture could not be found, so affected content may render with missing visuals.",
    "MISSING_MODEL": "A model could not be loaded, so affected content may render incorrectly or not at all.",
    "MISSING_SOUND": "A sound resource is unavailable, so affected sounds may be silent.",
    "CONFIG_REFERENCE": "A configuration references content that is not present, which can change or disable the related feature.",
    "CONFIG_DEFAULT_VALUE": "An invalid or missing configuration value was replaced with its default. This is usually recoverable, but may indicate an outdated config.",
    "REFERENCE_MAP": "A generated reference map could not be read. This can affect mixin or transformation resolution.",
    "MIXIN_DISABLED": "A mixin was disabled or cancelled. This may be harmless, but becomes relevant when related functionality also fails.",
    "RESOURCEPACK_INCOMPATIBLE": "A resource-pack feature was disabled because the pack is incompatible with that feature.",
    "NON_FABRIC_MOD": "A mod intended for another loader was detected in a Fabric environment and may not load correctly.",
    "OS_INCOMPATIBLE": "A component reports that the current operating system is unsupported for that feature.",
    "EXPRESSION_ERROR": "A resource expression could not be parsed, so the affected resource may fall back or behave unexpectedly.",
    "EVENT_HANDLER_ERROR": "A mod event handler could not be constructed during initialization, potentially disabling related startup logic.",
}

ROOT_CAUSE_RULES = {
    "DEPENDENCIA_REQUERIDA": (10, "A required dependency is explicitly reported as missing or incompatible.", "HIGH"),
    "VERSION_INCOMPATIBLE": (15, "An explicit version incompatibility is reported between loaded components.", "HIGH"),
    "INVALID_MOD": (20, "The loader explicitly reports an invalid or unreadable mod file.", "HIGH"),
    "DUPLICATE_MOD": (25, "The loader explicitly reports duplicate mod definitions.", "HIGH"),
    "CLASS_NOT_FOUND": (30, "A required class is missing, suggesting a dependency or version mismatch.", "MEDIUM"),
    "MIXIN_CONFLICT": (35, "A mixin injection conflict is explicitly reported.", "MEDIUM"),
    "MIXIN_NOT_FOUND": (40, "A mixin target is absent from the loaded environment.", "MEDIUM"),
    "MOD_LOAD_ERROR": (45, "A mod failed during loading or initialization.", "MEDIUM"),
    "REGISTRY_ERROR": (50, "A registry operation failed or unresolved mappings were reported.", "MEDIUM"),
    "EVENT_HANDLER_ERROR": (55, "A mod event handler failed during initialization.", "MEDIUM"),
    "EXCEPTION": (70, "A concrete exception is present in the log, but the available evidence does not prove it is the sole root cause.", "MEDIUM"),
    "WATCHDOG": (80, "The watchdog reports a stalled server tick.", "HIGH"),
    "CRASH": (100, "The log contains a Minecraft crash report, but no more specific upstream cause was established.", "MEDIUM"),
}

REGLAS_COMPILADAS = {
    tipo: re.compile(patron, re.I)
    for tipo, patron in REGLAS.items()
}

PATRON_MINECRAFT_FALLBACK = re.compile(
    r"^\s*Minecraft Version ID:\s*([0-9][\w.-]*)", re.I
)
PATRON_JAVA_LINE = re.compile(
    r"^\s*Java Version:\s*([0-9][\w.+-]*)", re.I
)
PATRON_JAVA_SIMPLE = re.compile(
    r"^\s*Java:\s*([0-9][\w.+-]*)", re.I
)
PATRON_JVM_VERSION = re.compile(
    r"JVM identified as .*?\b(?:version\s+)?([0-9]+(?:\.[0-9]+)+)", re.I
)
PATRON_FML_MC = re.compile(
    r"--fml\.mcVersion\s+([0-9][\w.-]*)", re.I
)
PATRON_FML_NEOFORGE = re.compile(
    r"--fml\.neoForgeVersion\s+([0-9][\w.-]*)", re.I
)
PATRON_FML_FORGE = re.compile(
    r"--fml\.forgeVersion\s+([0-9][\w.-]*)", re.I
)
PATRON_MOD_SECTION = re.compile(
    r"\b(?:fabric mods|mod list|loaded mods|loading \d+ mods)\b", re.I
)
PATRON_MOD_FALLBACK = re.compile(
    r"\b(?:mod|from mod|plugin for|by mod)\s+([A-Za-z0-9_.-]+)", re.I
)
PATRON_FORGE_MOD_FILE = re.compile(
    r"Found mod file\s+([^\s]+)\.jar\s+of type MOD", re.I
)
PATRON_REFERENCE_FILE = re.compile(
    r"[A-Za-z0-9_.-]+\.(?:json|properties|toml|json5|png|class|java|kt|jar)\b"
)
PATRON_CONFIG_DEFAULT = re.compile(
    r"Incorrect key\s+(.+?)\s+was corrected from\s+(.+?)\s+to its default", re.I
)
PATRON_CLASS_NOT_FOUND = re.compile(
    r"(?:ClassNotFoundException|NoClassDefFoundError):\s*([^\s\)]+)", re.I
)
PATRON_SHADER_RESOURCE = re.compile(
    r"(?:uniform|sampler)\s+(?:named\s+)?([A-Za-z0-9_]+)", re.I
)
PATRON_SOUND_RESOURCE = re.compile(
    r"(?:event|soundEvent)[: ]+([A-Za-z0-9_.:-]+)", re.I
)
STACK_SIGNAL_RE = re.compile(
    r"(?:caused by:|exception|error|warning|failed|missing|unable|could not|cannot|"
    r"mod|mixin|registry|config|recipe|advancement|loot|tag|resource|texture|"
    r"sound|shader|dependency|requires|depends|classnotfound|noclassdef|"
    r"\bat\s+[A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)*)",
    re.I
)
PATRON_TIMESTAMP = re.compile(r"^\[(?:(?:\d{2}:\d{2}:\d{2})(?:\.\d+)?|(?:\d{1,2}[A-Za-z]{3}\d{4}\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?))\]")
PATRON_NIVEL = re.compile(r"\[(?:[^\]]+/)?(INFO|WARN|WARNING|ERROR|DEBUG|TRACE|FATAL)\]", re.I)
PATRON_MINECRAFT = re.compile(r"(?:Loading Minecraft|Minecraft(?: Version| version|:)?|Minecraft Game Version)\s*[: ]\s*([0-9][\w.-]*)", re.I)
PATRON_FORGE_LOADING = re.compile(r"Forge mod loading, version\s+([0-9][\w.-]*)", re.I)
PATRON_FABRIC = re.compile(r"Fabric Loader(?: Version| version)?\s*[: ]\s*([0-9][\w.-]*)", re.I)
PATRON_FORGE = re.compile(r"(?:Forge|Forge Mod Loader)(?: Version| version)?\s*[: ]\s*([0-9][\w.-]*)", re.I)
PATRON_NEOFORGE = re.compile(r"NeoForge(?: Version| version)?\s*[: ]\s*([0-9][\w.-]*)", re.I)
PATRON_JAVA = re.compile(r"\b(?:Java|JVM|Java Version)\b\s*(?:version|runtime)?\s*[: ]\s*([0-9]+(?:\.[0-9]+)*(?:[-+][\w.-]+)?)", re.I)
PATRON_MOD_COUNT = re.compile(r"(?:Loading|Found|Loaded)\s+(\d+)\s+mods\b", re.I)
PATRON_EXCEPTION = re.compile(r"\b([A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)*(?:Exception|Error))\b")
PATRON_CAUSED_BY = re.compile(r"^\s*Caused by:\s*(.+)", re.I)
PATRON_NAMESPACE = re.compile(r"\b([a-zA-Z][a-zA-Z0-9_.-]{1,63}):([a-zA-Z0-9_.-]+)")
PATRON_LAG = re.compile(r"Running\s+(\d+(?:\.\d+)?)ms\s+or\s+(\d+)\s+ticks\s+behind", re.I)
PATRON_WATCHDOG_MS = re.compile(r"single server tick has taken\s+(\d+)\s+.*?\bmilliseconds", re.I)
PATRON_ENTITY = re.compile(r"Entity\s+([^\[]+)\[([^\]]*)\].*?removed=([A-Z_]+).*?wasn't found in section", re.I)
PATRON_BIOME = re.compile(r"Biome ['\"]?([a-zA-Z0-9_.-]+:[a-zA-Z0-9_.-]+)['\"]? does not exist", re.I)
PATRON_RESOURCEPACK = re.compile(r"Resource pack file/([^ ]+).*?not compatible with (.+?)(?:\.|$)", re.I)
PATRON_VERSION_WARN = re.compile(r"Mod\s+([a-zA-Z0-9_.-]+)\s+uses the version\s+([^ ]+).*?isn\'t compatible", re.I)
PATRON_CRASH_EXCEPTION_LINE = re.compile(
    r"^\s*([A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)*(?:Exception|Error))(?::\s*(.*))?$",
    re.I | re.M,
)
PATRON_STACK_FRAME = re.compile(
    r"^\s*at\s+([A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)*)\.",
    re.I | re.M,
)

def es_ruido(mensaje):
    return any(re.search(p, mensaje, re.I) for p in (
        r"Warnings were found!$",
        r"Removing existing FSB skies",
        r"FSB-Interop is converting .* resource packs",
        r"^Found \d+ mod(?:s)? in the game directory$",
    ))

def _nivel_normalizado(nivel):
    return "WARN" if nivel.upper() == "WARNING" else nivel.upper()

def es_linea_log(linea):
    return bool(PATRON_TIMESTAMP.search(linea) and PATRON_NIVEL.search(linea))

RULE_PRIORITY = (
    "CRASH", "WATCHDOG", "DEPENDENCIA_REQUERIDA", "DEPENDENCIA_RECOMENDADA",
    "MOD_LOAD_ERROR", "INVALID_MOD", "DUPLICATE_MOD", "VERSION_INCOMPATIBLE",
    "CLASS_NOT_FOUND", "EXPRESSION_ERROR", "EVENT_HANDLER_ERROR", "MIXIN_CONFLICT",
    "MIXIN_NOT_FOUND", "MIXIN_DISABLED", "MIXIN_ENABLED", "REGISTRY_ID_MISMATCH",
    "REGISTRY_VALUE_TYPE", "REGISTRY_ERROR", "RECIPE_ERROR", "ADVANCEMENT_ERROR",
    "LOOT_DATA_ERROR", "TAG_MISSING", "UNKNOWN_BLOCK", "MISSING_SOUND", "MISSING_MODEL",
    "MISSING_TEXTURE", "SHADER", "RESOURCEPACK_INCOMPATIBLE", "FANCYMENU", "GL_ERROR",
    "SOUND_ENGINE", "SERVER_LAG", "MOVEMENT", "ENTITY_NOT_FOUND", "ENTITY_ATTRIBUTE_ERROR",
    "NETWORK_TIMEOUT", "VERSION_FORMAT", "CONFIG_REFERENCE", "CONFIG_DEFAULT_VALUE",
    "MOD_METADATA", "RESOURCEPACK_WORKAROUND", "MISSING_DATAPACK_MOD", "MIXIN_CONFIG_WARNING",
    "CONFIG_OVERWRITE", "REFERENCE_MAP", "OS_INCOMPATIBLE", "WORLD_DATA", "NON_FABRIC_MOD",
    "OPTION_OVERRIDE", "DUPLICATE_UUID", "LOAD_TIME", "BROKEN_API", "LEGACY_MODE",
    "RESOURCE_FORMAT", "TEXTURE_SIZE", "PACK_FORMAT", "PARTIAL_INCOMPATIBILITY", "GC_WARNING",
    "NO_DATA_FIXER", "EXCEPTION",
)

def detectar_tipo(mensaje):
    for tipo in RULE_PRIORITY:
        if REGLAS_COMPILADAS[tipo].search(mensaje):
            return tipo
    return "OTRO"

def extraer_timestamp(linea):
    m = PATRON_TIMESTAMP.search(linea)
    if not m:
        return None
    raw = m.group(0)[1:-1]
    if " " in raw:
        return raw.split()[-1].split(".")[0]
    return raw.split(".")[0]

def extraer_nivel(linea):
    m = PATRON_NIVEL.search(linea)
    return _nivel_normalizado(m.group(1)) if m else None

def _primero(patrones, texto):
    for patron in patrones:
        m = patron.search(texto)
        if m:
            return m.group(1)
    return None

def extraer_metadata(lineas):
    metadata = {
        "minecraft": None,
        "loader": None,
        "loader_version": None,
        "java": None,
        "mods": 0,
    }

    for linea in lineas:
        if metadata["minecraft"] is None:
            metadata["minecraft"] = _primero(
                (PATRON_MINECRAFT, PATRON_MINECRAFT_FALLBACK),
                linea,
            )

        if metadata["loader_version"] is None:
            for patron, nombre in (
                (PATRON_NEOFORGE, "NeoForge"),
                (PATRON_FORGE_LOADING, "Forge"),
                (PATRON_FABRIC, "Fabric Loader"),
            ):
                match = patron.search(linea)
                if match:
                    metadata["loader"] = nombre
                    metadata["loader_version"] = match.group(1)
                    break

        if metadata["java"] is None:
            match = PATRON_JAVA_LINE.search(linea)
            if not match:
                match = PATRON_JVM_VERSION.search(linea)
            if not match:
                match = PATRON_JAVA_SIMPLE.search(linea)
            if match:
                metadata["java"] = match.group(1)

        if not metadata["mods"]:
            match = PATRON_MOD_COUNT.search(linea)
            if match:
                metadata["mods"] = int(match.group(1))

        if all((
            metadata["minecraft"],
            metadata["loader_version"],
            metadata["java"],
            metadata["mods"],
        )):
            break

    return metadata

def _add_mod(mods, vistos, mod_id, version):
    mod_id = mod_id.strip().strip("[](),")
    version = version.strip().strip("[](),")
    if not re.fullmatch(r"[A-Za-z0-9_.-]{2,80}", mod_id):
        return
    if mod_id.lower() in {"minecraft", "java", "fabricloader", "fabric-loader", "forge", "neoforge", "root", "unsupported", "loader", "mod"}:
        return
    key = mod_id.lower()
    if key not in vistos:
        vistos.add(key)
        mods.append({"id": mod_id, "version": version or None})

def extraer_mods(lineas, _count_only=False):
    mods = []
    forge_mods = []
    vistos = set()
    forge_vistos = set()
    patterns = (
        re.compile(r"^\s*[-*]\s+([A-Za-z0-9_.-]{2,80})\s+([^\s]+)", re.I),
        re.compile(r"^\s*([A-Za-z0-9_.-]{2,80})\s*\|\s*([^\s|]+)", re.I),
        re.compile(r"^\s*([A-Za-z0-9_.-]{2,80})\s+([0-9][^\s]*)\s*$", re.I),
        re.compile(r"^\s*([A-Za-z0-9_.-]{2,80})\s+([0-9][^\s]*)\s+\(", re.I),
    )

    in_section = False

    for linea in lineas:
        low = linea.lower()

        forge_mod = PATRON_FORGE_MOD_FILE.search(linea)
        if forge_mod:
            _add_mod(
                forge_mods,
                forge_vistos,
                forge_mod.group(1),
                "unknown",
            )

        if PATRON_MOD_SECTION.search(low):
            in_section = True

        if in_section:
            for patron in patterns:
                match = patron.match(linea)
                if match:
                    _add_mod(
                        mods,
                        vistos,
                        match.group(1),
                        match.group(2),
                    )
                    break

        if (
            in_section
            and PATRON_TIMESTAMP.search(linea)
            and not PATRON_MOD_SECTION.search(low)
            and mods
        ):
            break

    if not mods and forge_mods:
        mods = forge_mods
        vistos = {mod["id"].lower() for mod in mods}

    if not mods and forge_mods:
        mods = forge_mods

    if not mods and forge_mods:
        mods = forge_mods
        vistos = {mod["id"].lower() for mod in mods}

    if not mods:
        for linea in lineas:
            match = PATRON_MOD_FALLBACK.search(linea)
            if (
                match
                and match.group(1).lower()
                not in {"file", "mod", "plugin", "from", "for", "the"}
            ):
                _add_mod(mods, vistos, match.group(1), "unknown")

    return mods

class ModMatcher:
    def __init__(self, mods):
        self.ids = {
            mod["id"].lower(): mod["id"]
            for mod in mods
            if mod.get("id")
        }
        self.pattern = None

        if self.ids:
            alternatives = sorted(
                (re.escape(key) for key in self.ids),
                key=len,
                reverse=True,
            )
            self.pattern = re.compile(
                r"(?<![A-Za-z0-9_.-])(?:"
                + "|".join(alternatives)
                + r")(?![A-Za-z0-9_.-])",
                re.I,
            )

    def find(self, texto):
        if not self.pattern or not texto:
            return []

        encontrados = set()
        for match in self.pattern.finditer(texto):
            canonical = self.ids.get(match.group(0).lower())
            if canonical:
                encontrados.add(canonical)

        return sorted(encontrados)


def detectar_mods_relacionados(texto, mods):
    return ModMatcher(mods).find(texto)


def _mods_relacionados(texto, matcher):
    return matcher.find(texto) if matcher else []

def extraer_dependencias(texto):
    resultado, vistos = [], set()
    patrones = [
        ("required", re.compile(r"(?:missing required dependency|missing dependency|requires .*?(?:version|mod)|depends on)\s*:?\s*([A-Za-z0-9_.-]+)", re.I)),
        ("recommended", re.compile(r"(?:recommends .*?(?:version|mod)|optional dependency)\s*:?\s*([A-Za-z0-9_.-]+)", re.I)),
    ]
    for relacion, patron in patrones:
        for m in patron.finditer(texto):
            dep = m.group(1)
            if dep.lower() not in vistos:
                vistos.add(dep.lower())
                resultado.append({"tipo": dep, "relacion": relacion})
    return resultado

def extraer_excepciones(texto):
    resultado = []
    for m in PATRON_EXCEPTION.finditer(texto):
        nombre = m.group(1)
        if nombre not in resultado:
            resultado.append(nombre)
    return resultado

def extraer_causas(texto):
    resultado = []
    for linea in texto.splitlines():
        m = PATRON_CAUSED_BY.search(linea)
        if m and m.group(1).strip() not in resultado:
            resultado.append(m.group(1).strip())
    return resultado

def extraer_referencias(texto):
    refs = []
    vistos = set()

    for match in PATRON_NAMESPACE.finditer(texto):
        ref = f"{match.group(1)}:{match.group(2)}"
        if ref not in vistos:
            vistos.add(ref)
            refs.append(ref)
            if len(refs) >= 50:
                return refs

    for match in PATRON_REFERENCE_FILE.finditer(texto):
        ref = match.group(0)
        if ref not in vistos:
            vistos.add(ref)
            refs.append(ref)
            if len(refs) >= 50:
                break

    return refs

def normalizar_mensaje(tipo, mensaje):
    texto = mensaje.strip()
    if tipo == "CONFIG_DEFAULT_VALUE":
        m = re.search(r"Incorrect key\s+(.+?)\s+was corrected from\s+(.+?)\s+to its default", texto, re.I)
        return f"Configuration default value: {m.group(1).strip()}" if m else "Configuration default value applied"
    if tipo == "CRASH":
        m = PATRON_EXCEPTION.search(texto)
        return f"Crash report: {m.group(1)}" if m else "Minecraft crash detected"
    fixed = {
        "NO_DATA_FIXER": "No data fixer registered",
        "BROKEN_API": "Broken mod API implementation",
        "LEGACY_MODE": "Mod/plugin running in legacy mode",
        "RESOURCE_FORMAT": "Resource file naming format warning",
        "TEXTURE_SIZE": "Texture mipmap limitation",
        "PACK_FORMAT": "Resource pack format fallback",
        "PARTIAL_INCOMPATIBILITY": "Partial mod incompatibility detected",
        "GC_WARNING": "Garbage collector warning",
        "DEPENDENCIA_REQUERIDA": "Required dependency missing or incompatible",
        "DEPENDENCIA_RECOMENDADA": "Recommended dependency missing",
        "MOD_LOAD_ERROR": "Mod loading error",
        "MOD_METADATA": "Mod metadata file missing or incomplete",
        "RESOURCEPACK_WORKAROUND": "Resource pack compatibility workaround",
        "MISSING_DATAPACK_MOD": "Missing data pack mod",
        "REGISTRY_ID_MISMATCH": "Registry ID mismatch",
        "MIXIN_CONFIG_WARNING": "Mixin configuration warning",
        "INVALID_MOD": "Invalid or unreadable mod file",
        "DUPLICATE_MOD": "Duplicate mod detected",
        "VERSION_INCOMPATIBLE": "Mod/game/loader version incompatibility",
        "REGISTRY_ERROR": "Registry loading or registration error",
        "REGISTRY_ID_MISMATCH": "Registry ID mismatch",
        "RECIPE_ERROR": "Recipe error",
        "ADVANCEMENT_ERROR": "Advancement error",
        "TAG_MISSING": "Missing data pack tags",
        "DUPLICATE_UUID": "Duplicate entity UUID",
        "MISSING_TEXTURE": "Missing texture",
        "MIXIN_CONFLICT": "Mixin conflict",
        "MIXIN_NOT_FOUND": "Mixin target not found",
        "MIXIN_DISABLED": "Mixin disabled or cancelled",
        "MIXIN_ENABLED": "Mixin force-enabled",
        "CONFIG_OVERWRITE": "Configuration value overwritten",
        "REFERENCE_MAP": "Reference map could not be read",
        "OS_INCOMPATIBLE": "Operating system incompatibility",
        "WORLD_DATA": "World region folder not found",
        "NON_FABRIC_MOD": "Non-Fabric mod detected",
        "OPTION_OVERRIDE": "Mod option override",
        "REGISTRY_VALUE_TYPE": "Invalid performance counter value type",
        "FANCYMENU": "FancyMenu resource error",
        "GL_ERROR": "OpenGL/GLFW error",
        "SOUND_ENGINE": "Sound engine error",
        "SERVER_LAG": "Server tick delay",
        "MOVEMENT": "Player movement exceeded server threshold",
        "ENTITY_NOT_FOUND": "Entity not found in section",
        "ENTITY_ATTRIBUTE_ERROR": "Entity attribute registration error",
        "NETWORK_TIMEOUT": "Network timeout or disconnection",
        "VERSION_FORMAT": "Non-standard mod version",
        "CONFIG_REFERENCE": "Configuration references missing content",
        "UNKNOWN_BLOCK": "Unknown block or blockstate",
        "MISSING_MODEL": "Missing model",
        "MISSING_SOUND": "Missing sound",
        "SHADER": "Shader resource mismatch",
        "RESOURCEPACK_INCOMPATIBLE": "Resource pack incompatibility",
        "LOAD_TIME": "Long load time",
        "LOOT_DATA_ERROR": "Loot data parsing error",
        "EXPRESSION_ERROR": "Expression parsing error",
        "EVENT_HANDLER_ERROR": "Event handler construction error",
    }
    if tipo in fixed:
        return fixed[tipo]
    if tipo == "CLASS_NOT_FOUND":
        m = re.search(r"(?:ClassNotFoundException|NoClassDefFoundError):\s*([^\s\)]+)", texto, re.I)
        return f"Class not found: {m.group(1)}" if m else "Class not found"
    if tipo == "SERVER_LAG":
        m = PATRON_LAG.search(texto)
        return f"Server tick delay: {m.group(1)} ms / {m.group(2)} ticks behind" if m else "Server tick delay"
    if tipo == "WATCHDOG":
        m = PATRON_WATCHDOG_MS.search(texto)
        return f"Server watchdog: tick took {m.group(1)} ms" if m else "Server watchdog detected a stalled tick"
    if tipo == "SHADER":
        m = re.search(r"(?:uniform|sampler)\s+(?:named\s+)?([A-Za-z0-9_]+)", texto, re.I)
        return f"Shader resource mismatch: {m.group(1)}" if m else "Shader resource mismatch"
    if tipo == "MISSING_SOUND":
        m = re.search(r"(?:event|soundEvent)[: ]+([A-Za-z0-9_.:-]+)", texto, re.I)
        return f"Missing sound: {m.group(1)}" if m else "Missing sound"
    return texto

def importancia(tipo, nivel, ocurrencias=1):
    if tipo in {"CRASH", "WATCHDOG"}:
        return "CRITICAL"
    if tipo in {"MOD_LOAD_ERROR", "INVALID_MOD", "DUPLICATE_MOD", "VERSION_INCOMPATIBLE", "CLASS_NOT_FOUND", "DEPENDENCIA_REQUERIDA", "MIXIN_CONFLICT", "MIXIN_NOT_FOUND", "REGISTRY_ERROR", "RECIPE_ERROR", "ADVANCEMENT_ERROR", "EVENT_HANDLER_ERROR"}:
        return "HIGH"
    if tipo in {"SERVER_LAG", "SOUND_ENGINE", "GL_ERROR", "SHADER", "UNKNOWN_BLOCK", "MISSING_MODEL", "MISSING_SOUND", "MISSING_TEXTURE", "NETWORK_TIMEOUT", "MOVEMENT", "ENTITY_NOT_FOUND", "FANCYMENU", "CONFIG_REFERENCE", "LOOT_DATA_ERROR", "TAG_MISSING", "MIXIN_DISABLED", "OS_INCOMPATIBLE", "NON_FABRIC_MOD", "EXPRESSION_ERROR", "RESOURCEPACK_INCOMPATIBLE", "REGISTRY_ID_MISMATCH"}:
        return "MEDIUM"
    if tipo in {"DEPENDENCIA_RECOMENDADA", "MIXIN_ENABLED", "CONFIG_DEFAULT_VALUE", "MIXIN_CONFIG_WARNING", "CONFIG_OVERWRITE", "REFERENCE_MAP", "RESOURCEPACK_WORKAROUND", "MISSING_DATAPACK_MOD", "WORLD_DATA", "OPTION_OVERRIDE", "LOAD_TIME", "BROKEN_API", "LEGACY_MODE", "RESOURCE_FORMAT", "TEXTURE_SIZE", "PACK_FORMAT", "PARTIAL_INCOMPATIBILITY", "GC_WARNING", "NO_DATA_FIXER", "MOD_METADATA", "VERSION_FORMAT"}:
        return "LOW"
    return "LOW" if nivel in {"WARN", "WARNING"} else "MEDIUM"

def diagnostico(tipo, problema):
    texts = {
        "CRASH": "Minecraft generated a crash report. The root exception and stack trace are the main clues for locating the failure.",
        "WATCHDOG": "A server tick exceeded the watchdog threshold, indicating a blocked or extremely slow task.",
        "MOD_LOAD_ERROR": "One or more mods failed during loading or initialization.",
        "INVALID_MOD": "The loader could not parse or accept one of the mod files.",
        "DUPLICATE_MOD": "The environment contains more than one copy or definition of the same mod.",
        "VERSION_INCOMPATIBLE": "The log indicates an incompatibility between Minecraft, loader, mod, or dependency versions.",
        "CLASS_NOT_FOUND": "A required class is unavailable. This usually points to a missing dependency, incompatible version, or incomplete integration.",
        "DEPENDENCIA_REQUERIDA": "The log indicates that a required dependency is missing or incompatible.",
        "DEPENDENCIA_RECOMENDADA": "The mod declares a recommended dependency; this normally does not prevent startup.",
        "MIXIN_CONFLICT": "Multiple mixins target the same code or an injection could not be applied.",
        "MIXIN_NOT_FOUND": "A mixin targets code that could not be found in the loaded version.",
        "MIXIN_DISABLED": "The loader disabled or cancelled a mixin. This alone does not prove a severe failure.",
        "REGISTRY_ERROR": "A registry operation or registration step failed.",
        "RECIPE_ERROR": "A recipe could not be registered or parsed.",
        "ADVANCEMENT_ERROR": "An advancement could not be registered or parsed.",
        "LOOT_DATA_ERROR": "A loot resource contains a reference or structure that could not be resolved.",
        "TAG_MISSING": "A data pack or mod references tags that are not present.",
        "UNKNOWN_BLOCK": "The log references a block, property, or content that could not be resolved.",
        "MISSING_SOUND": "Minecraft attempted to load or play a sound that is unavailable.",
        "MISSING_MODEL": "Minecraft could not load or build a required model.",
        "MISSING_TEXTURE": "Minecraft could not find a required texture.",
        "SHADER": "A shader requests a resource that is unavailable in the loaded program.",
        "RESOURCEPACK_INCOMPATIBLE": "A resource pack is incompatible with a specific feature and that feature was disabled.",
        "SERVER_LAG": "The server is not processing ticks on time.",
        "MOVEMENT": "The server received movement beyond the expected threshold; lag or desynchronization can cause this.",
        "ENTITY_NOT_FOUND": "An entity was requested from a section where it no longer exists.",
        "ENTITY_ATTRIBUTE_ERROR": "An entity was registered without the attributes expected by its entity definition.",
        "NETWORK_TIMEOUT": "A network connection or resource did not respond within the expected time.",
        "CONFIG_DEFAULT_VALUE": "The system found a missing or invalid configuration key and applied its default value.",
        "CONFIG_REFERENCE": "A configuration references content that is not present in the loaded environment.",
        "CONFIG_OVERWRITE": "A component overwrote a configuration value that already contained data.",
        "REFERENCE_MAP": "A generated reference map used by mixins or another subsystem could not be read.",
        "NO_DATA_FIXER": "No DataFixer is registered for that content. In mods this can be a normal message.",
        "NON_FABRIC_MOD": "Fabric detected a mod that does not belong to the expected Fabric environment.",
        "MOD_METADATA": "The loader found a mod file without expected metadata. In Forge this can correspond to internal libraries and does not necessarily mean a broken mod.",
        "RESOURCEPACK_WORKAROUND": "A mod is using a resource-loading path considered incorrect by the loader, so a workaround was applied.",
        "MISSING_DATAPACK_MOD": "The environment references a mod as a data pack provider, but that content is unavailable.",
        "REGISTRY_ID_MISMATCH": "A registered object requested a different ID than the one it received. If widespread, this can indicate registry differences between components.",
        "MIXIN_CONFIG_WARNING": "A mixin configuration does not declare an expected property. This alone does not indicate a crash.",
        "EXPRESSION_ERROR": "A resource expression could not be parsed and the system fell back to a default value.",
        "EVENT_HANDLER_ERROR": "An event handler could not be constructed during mod initialization.",
    }
    return texts.get(tipo) or f"The log contains a {TYPE_LABELS.get(tipo, tipo).lower()} signal that may require investigation depending on context."


def recomendacion(tipo, problema):
    texts = {
        "CRASH": "Review the root exception and the first mod classes in the stack trace before changing multiple mods at once.",
        "WATCHDOG": "Review the watchdog stack trace and the events immediately preceding the slow tick.",
        "MOD_LOAD_ERROR": "Review the mod named in the error and its dependencies and compatibility with the game and loader versions.",
        "INVALID_MOD": "Check that the file is a valid mod for the selected loader and Minecraft version.",
        "DUPLICATE_MOD": "Keep only one copy of each mod and check for duplicate versions.",
        "VERSION_INCOMPATIBLE": "Check the Minecraft, loader, mod, and dependency versions named in the message.",
        "CLASS_NOT_FOUND": "Check the dependency, version, and loader of the mod requesting the class.",
        "DEPENDENCIA_REQUERIDA": "Verify that the required dependency is installed and compatible.",
        "DEPENDENCIA_RECOMENDADA": "Install it only if the recommended functionality is needed or another error points to it.",
        "MIXIN_CONFLICT": "Identify the mods involved in the conflict and check versions and compatibility before removing anything.",
        "MIXIN_NOT_FOUND": "Check that the mod and its version match the loaded Minecraft version.",
        "REGISTRY_ERROR": "Review the first registry or mod mentioned and the lines immediately preceding the error.",
        "RECIPE_ERROR": "Identify the recipe and the mod that provides it; check format changes or dependencies.",
        "ADVANCEMENT_ERROR": "Identify the advancement and the mod or data pack that provides it.",
        "LOOT_DATA_ERROR": "Identify the resource namespace and check the version of the mod providing it.",
        "UNKNOWN_BLOCK": "Identify the namespace and check which mod or data pack should provide the content.",
        "MISSING_SOUND": "Identify the sound namespace and check the installation of the mod or resource pack providing it.",
        "MISSING_MODEL": "Identify the resource and check that the mod or resource pack is complete.",
        "MISSING_TEXTURE": "Identify the resource and check that the mod or resource pack is complete.",
        "SERVER_LAG": "Review which tasks coincide with the lag spikes before changing mods.",
        "ENTITY_ATTRIBUTE_ERROR": "Check the mod that registers the entity and its compatibility with the current Minecraft version.",
        "CONFIG_DEFAULT_VALUE": "Do not manually correct every key; check whether the configuration belongs to an older mod version.",
        "MOD_METADATA": "Check whether the file belongs to a loader library before modifying it.",
        "RESOURCEPACK_WORKAROUND": "Do not change mods solely because of this warning; check whether the workaround coincides with other resource errors.",
        "MISSING_DATAPACK_MOD": "Check whether the mod providing the data pack is installed or whether the reference belongs to an old configuration.",
        "REGISTRY_ID_MISMATCH": "If widespread, review versions of mods registering the content and changes to the mod list.",
        "MIXIN_CONFIG_WARNING": "Do not change versions solely because of this warning; review other mixin errors if present.",
        "EXPRESSION_ERROR": "Identify the resource or mod that generated the expression and check its configuration or version.",
        "EVENT_HANDLER_ERROR": "Review the first exception and mod mentioned around the event handler failure.",
    }
    return texts.get(tipo)

def _base_problema(nivel, tipo, hora, linea, mensaje, matcher):
    return {
        "nivel": nivel,
        "tipo": tipo,
        "hora": hora,
        "linea": linea,
        "componente": extraer_componente(mensaje),
        "mensaje": mensaje,
        "mensaje_normalizado": normalizar_mensaje(tipo, mensaje),
        "ocurrencias": 1,
        "excepciones": extraer_excepciones(mensaje),
        "causas": extraer_causas(mensaje),
        "mods_relacionados": _mods_relacionados(mensaje, matcher),
        "dependencias": extraer_dependencias(mensaje),
        "referencias": extraer_referencias(mensaje),
        "stack_trace": [],
        "evidence": [{"line": linea, "text": mensaje}],
        "severity": importancia(tipo, nivel),
    }


def extraer_componente(mensaje):
    m = re.search(r"\[[^\]]+\]\s+\[[^\]]+/([^\]]+)\]", mensaje)
    return m.group(1) if m else None


def _append_unique(target, values):
    for value in values:
        if value not in target:
            target.append(value)


def _analyze_stack_line(linea, problema, matcher):
    stripped = linea.strip()
    if not stripped:
        return

    problema["stack_trace"].append(linea.rstrip())

    if not STACK_SIGNAL_RE.search(stripped):
        return

    _append_unique(problema["excepciones"], extraer_excepciones(stripped))
    _append_unique(problema["causas"], extraer_causas(stripped))
    evidence = {"line": problema.get("linea"), "text": linea.rstrip()}
    if evidence not in problema.get("evidence", []) and len(problema.get("evidence", [])) < 8:
        problema.setdefault("evidence", []).append(evidence)
    _append_unique(problema["mods_relacionados"], _mods_relacionados(stripped, matcher))
    _append_unique(problema["dependencias"], extraer_dependencias(stripped))
    _append_unique(problema["referencias"], extraer_referencias(stripped))


def analizar_problemas(lineas, mods, progress_callback=None):
    problemas = []
    actual = None
    matcher = ModMatcher(mods)
    total = max(len(lineas), 1)
    last_progress = -1

    for numero, linea in enumerate(lineas, 1):
        timestamp_match = PATRON_TIMESTAMP.search(linea)

        if timestamp_match:
            nivel_match = PATRON_NIVEL.search(linea)

            if nivel_match:
                if actual:
                    problemas.append(actual)

                actual = None
                nivel = _nivel_normalizado(nivel_match.group(1))

                if nivel not in {"ERROR", "WARN", "FATAL"}:
                    continue

                mensaje = linea.strip()

                if es_ruido(mensaje):
                    continue

                tipo = detectar_tipo(mensaje)
                timestamp = extraer_timestamp(linea)

                actual = _base_problema(
                    nivel,
                    tipo,
                    timestamp,
                    numero,
                    mensaje,
                    matcher,
                )
                continue

        if actual:
            _analyze_stack_line(linea, actual, matcher)

        if progress_callback:
            progress = 25 + int((numero / total) * 60)
            if progress != last_progress:
                last_progress = progress
                progress_callback(progress, "Analyzing log entries")

    if actual:
        problemas.append(actual)

    return problemas

def _crash_report_problem(lineas, mods):
    text = "\n".join(lineas)
    crash_marker = re.search(
        r"Preparing crash report(?: with UUID)?|#@!@#\s*(?:Game|Server) crashed!?(?:\s+Crash report saved to:)?|---- Minecraft Crash Report ----",
        text,
        re.I,
    )
    if not crash_marker:
        return None

    report_start = text.lower().find("---- minecraft crash report ----")
    report_text = text[report_start:] if report_start >= 0 else text

    desc = re.search(
        r"^\s*Description:\s*(.+)$",
        report_text,
        re.I | re.M,
    )
    exc_match = PATRON_CRASH_EXCEPTION_LINE.search(report_text)
    exception_name = exc_match.group(1) if exc_match else None
    exception_detail = exc_match.group(2).strip() if exc_match and exc_match.group(2) else None

    matcher = ModMatcher(mods)
    related_mods = _mods_relacionados(report_text, matcher)

    context_candidates = [
        text.rfind("Reported exception thrown!", 0, report_start if report_start >= 0 else len(text)),
        text.rfind("Caused by:", 0, report_start if report_start >= 0 else len(text)),
    ]
    context_start = max(context_candidates)
    crash_context = text[context_start:] if context_start >= 0 else report_text

    first_mod_frame = None
    ignored_prefixes = (
        "net.minecraft.", "java.", "javax.", "jdk.", "sun.",
        "com.mojang.", "cpw.mods.", "net.minecraftforge.",
        "org.spongepowered.", "org.apache.",
    )
    for frame in PATRON_STACK_FRAME.finditer(crash_context):
        class_name = frame.group(1)
        if not class_name.startswith(ignored_prefixes):
            first_mod_frame = class_name
            break

    frame_mod = None
    if first_mod_frame:
        lowered_frame = first_mod_frame.lower()
        frame_line = next((line for line in crash_context.splitlines() if first_mod_frame in line and line.strip().startswith("at ")), "")
        jar_match = re.search(r"(?:~\[|\[)([^\]]+?\.jar)", frame_line, re.I)
        jar_stem = jar_match.group(1).rsplit("/", 1)[-1].rsplit("\\", 1)[-1].removesuffix(".jar").lower() if jar_match else ""
        frame_tokens = set(re.findall(r"[a-z0-9]+", lowered_frame))
        for mod in mods:
            mod_id = str(mod.get("id", "") if isinstance(mod, dict) else mod).lower()
            mod_tokens = set(re.findall(r"[a-z0-9]+", mod_id))
            if mod_id and mod_id in lowered_frame:
                frame_mod = mod_id
                break
            if jar_stem and (jar_stem.startswith(mod_id) or mod_id.startswith(jar_stem)):
                frame_mod = mod_id
                break
            if frame_tokens & mod_tokens:
                shared = frame_tokens & mod_tokens
                if any(len(token) >= 4 for token in shared):
                    frame_mod = mod_id
                    break
        if not frame_mod:
            package_tokens = [token for token in re.findall(r"[a-z0-9]+", lowered_frame) if len(token) >= 4]
            if jar_stem:
                jar_tokens = [token for token in re.findall(r"[a-z0-9]+", jar_stem) if len(token) >= 4]
                for token in jar_tokens:
                    if token in package_tokens:
                        frame_mod = token
                        break

    resumen = desc.group(1).strip() if desc else "Minecraft crash report"
    if exception_name:
        mensaje = f"Crash report: {exception_name}"
    else:
        mensaje = f"Crash report: {resumen}"

    marker_line_number = next((i for i, line in enumerate(lineas, 1) if crash_marker.group(0) in line), 1)
    marker_line = lineas[marker_line_number - 1] if marker_line_number else ""
    p = _base_problema(
        "ERROR",
        "CRASH",
        extraer_timestamp(marker_line),
        marker_line_number,
        mensaje,
        matcher,
    )
    p["excepciones"] = extraer_excepciones(report_text)
    p["causas"] = extraer_causas(report_text)
    p["referencias"] = extraer_referencias(report_text)
    p["mods_relacionados"] = related_mods
    p["crash_description"] = resumen
    p["crash_exception"] = exception_name
    p["crash_exception_detail"] = exception_detail
    p["crash_stack_frame"] = first_mod_frame
    p["crash_mod"] = frame_mod
    p["stack_trace"] = lineas[:500]
    p["evidence"] = []

    for index, line in enumerate(lineas, 1):
        if crash_marker.group(0) in line or "---- Minecraft Crash Report ----" in line:
            p["evidence"].append({"line": index, "text": line.rstrip()})
        if len(p["evidence"]) >= 2:
            break

    for index, line in enumerate(lineas, 1):
        if exception_name and exception_name in line:
            item = {"line": index, "text": line.rstrip()}
            if item not in p["evidence"] and len(p["evidence"]) < 8:
                p["evidence"].append(item)
            break

    if first_mod_frame:
        for index, line in enumerate(lineas, 1):
            if first_mod_frame in line and line.strip().startswith("at "):
                item = {"line": index, "text": line.rstrip()}
                if item not in p["evidence"] and len(p["evidence"]) < 8:
                    p["evidence"].append(item)
                break

    for index, line in enumerate(lineas, 1):
        if PATRON_CAUSED_BY.search(line):
            item = {"line": index, "text": line.rstrip()}
            if item not in p["evidence"] and len(p["evidence"]) < 8:
                p["evidence"].append(item)
            break

    return p

def agrupar_problemas(problemas):
    grupos = {}
    for problema in problemas:
        tipo = problema["tipo"]
        clave = (problema["nivel"], tipo, problema["mensaje_normalizado"])
        if clave not in grupos:
            grupos[clave] = {
                "nivel": problema["nivel"], "tipo": tipo, "tipo_nombre": TYPE_LABELS.get(tipo, tipo), "hora": problema["hora"], "linea": problema["linea"],
                "componente": problema["componente"], "mensaje": problema["mensaje"],
                "mensaje_normalizado": problema["mensaje_normalizado"], "ocurrencias": 0,
                "primera_aparicion": problema["hora"], "ultima_aparicion": problema["hora"], "lineas": [],
                "componentes": [], "excepciones": [], "causas": [], "mods_relacionados": [],
                "dependencias": [], "referencias": [], "stack_trace": [], "evidence": [],
                "crash_description": problema.get("crash_description"),
                "crash_exception": problema.get("crash_exception"),
                "crash_exception_detail": problema.get("crash_exception_detail"),
                "crash_stack_frame": problema.get("crash_stack_frame"),
                "crash_mod": problema.get("crash_mod"),
            }
        g = grupos[clave]
        g["ocurrencias"] += problema["ocurrencias"]
        if problema["hora"]:
            g["ultima_aparicion"] = problema["hora"]
        if problema["linea"] not in g["lineas"]:
            g["lineas"].append(problema["linea"])
        if problema["componente"] and problema["componente"] not in g["componentes"]:
            g["componentes"].append(problema["componente"])
        for key in ("excepciones", "causas", "mods_relacionados", "dependencias", "referencias"):
            for value in problema[key]:
                if value not in g[key]:
                    g[key].append(value)
        if problema["stack_trace"] and not g["stack_trace"]:
            g["stack_trace"] = problema["stack_trace"]
        for evidence in problema.get("evidence", []):
            if evidence not in g["evidence"] and len(g["evidence"]) < 8:
                g["evidence"].append(evidence)
    for g in grupos.values():
        g["importancia"] = importancia(g["tipo"], g["nivel"], g["ocurrencias"])
        g["severity"] = g["importancia"]
        g["diagnostico"] = diagnostico(g["tipo"], g)
        g["why_this_matters"] = WHY_THIS_MATTERS.get(g["tipo"], diagnostico(g["tipo"], g))
        g["recomendacion"] = recomendacion(g["tipo"], g) or "Review the evidence and surrounding log entries before making changes."
        g["root_cause"] = None
    return list(grupos.values())

def _root_cause_candidate(problemas):
    candidates = []
    crash_problems = [p for p in problemas if p.get("tipo") == "CRASH"]

    # If a concrete loader/dependency failure occurs immediately around the
    # crash marker, it is more useful than merely repeating the crash report.
    nearby_types = {
        "DEPENDENCIA_REQUERIDA", "VERSION_INCOMPATIBLE", "INVALID_MOD",
        "DUPLICATE_MOD", "MOD_LOAD_ERROR", "EVENT_HANDLER_ERROR",
    }
    if crash_problems:
        crash_line = min(
            (p.get("linea") or 10**12 for p in crash_problems),
            default=10**12,
        )
        for problem in problemas:
            if problem.get("tipo") not in nearby_types:
                continue
            line = problem.get("linea") or 10**12
            if line <= crash_line and crash_line - line <= 25:
                priority, summary, confidence = ROOT_CAUSE_RULES[problem["tipo"]]
                candidates.append((priority, 0, -problem.get("ocurrencias", 1), problem, summary, confidence))

        if candidates:
            candidates.sort(key=lambda x: x[:3])
            _, _, _, problem, summary, confidence = candidates[0]
            return {
                "status": "probable",
                "confidence": confidence,
                "summary": summary,
                "problem_type": problem.get("tipo"),
                "message": problem.get("mensaje_normalizado") or problem.get("mensaje"),
                "mods": list(problem.get("mods_relacionados", [])),
                "evidence": list(problem.get("evidence", []))[:5],
            }

        crash = crash_problems[0]
        exception_name = crash.get("crash_exception")
        exception_detail = crash.get("crash_exception_detail")
        description = crash.get("crash_description")
        crash_mod = crash.get("crash_mod")
        frame = crash.get("crash_stack_frame")

        if crash_mod and frame:
            summary = (
                f"The crash report identifies {exception_name or 'an exception'} during "
                f"{description or 'runtime execution'}. The first mod-owned stack frame "
                f"points to {crash_mod} ({frame}). This is strong evidence of involvement, "
                "not proof that the mod is solely responsible."
            )
            confidence = "MEDIUM"
        elif exception_name:
            summary = (
                f"The crash report identifies {exception_name}"
                f"{': ' + exception_detail if exception_detail else ''}"
                f" during {description or 'runtime execution'}. "
                "This identifies the immediate failure, but the log does not establish a unique mod owner."
            )
            confidence = "HIGH"
        else:
            summary = "The log contains a confirmed Minecraft crash report, but its underlying owner could not be established from the available evidence."
            confidence = "MEDIUM"

        return {
            "status": "probable",
            "confidence": confidence,
            "summary": summary,
            "problem_type": "CRASH",
            "message": crash.get("mensaje_normalizado") or crash.get("mensaje"),
            "mods": [crash_mod] if crash_mod else list(crash.get("mods_relacionados", []))[:5],
            "evidence": list(crash.get("evidence", []))[:5],
        }

    for problem in problemas:
        tipo = problem.get("tipo")
        if tipo in ROOT_CAUSE_RULES:
            priority, summary, confidence = ROOT_CAUSE_RULES[tipo]
            candidates.append((priority, 0 if confidence == "HIGH" else 1, -problem.get("ocurrencias", 1), problem, summary, confidence))
        elif problem.get("excepciones") and tipo == "EXCEPTION":
            candidates.append((70, 1, -problem.get("ocurrencias", 1), problem, "A concrete exception is present, but the log does not prove that it is the sole root cause.", "MEDIUM"))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[:3])
    _, _, _, problem, summary, confidence = candidates[0]
    return {
        "status": "probable" if confidence in {"HIGH", "MEDIUM"} else "uncertain",
        "confidence": confidence,
        "summary": summary,
        "problem_type": problem.get("tipo"),
        "message": problem.get("mensaje_normalizado") or problem.get("mensaje"),
        "mods": list(problem.get("mods_relacionados", [])),
        "evidence": list(problem.get("evidence", []))[:5],
    }

def enrich_root_causes(problemas):
    candidate = _root_cause_candidate(problemas)
    for problem in problemas:
        problem["root_cause"] = None
    if candidate:
        for problem in problemas:
            if problem.get("tipo") == candidate["problem_type"]:
                problem["root_cause"] = dict(candidate)
    return candidate

def build_analysis_summary(metadata, mods, problemas, crash):
    severities = {level: 0 for level in ("CRITICAL", "HIGH", "MEDIUM", "LOW")}
    for problem in problemas:
        severity = problem.get("severity") or problem.get("importancia") or "LOW"
        severities.setdefault(severity, 0)
        severities[severity] += 1
    root = _root_cause_candidate(problemas)
    if root:
        headline = root["summary"]
    elif problemas:
        headline = "The log contains multiple signals, but no single probable root cause was established from the available evidence."
    else:
        headline = "No grouped error or warning signals were detected in the analyzed log."
    return {
        "headline": headline,
        "root_cause": root,
        "severity_counts": severities,
        "problem_count": len(problemas),
        "error_occurrences": sum(p.get("ocurrencias", 1) for p in problemas if p.get("nivel") in {"ERROR", "FATAL"}),
        "warning_occurrences": sum(p.get("ocurrencias", 1) for p in problemas if p.get("nivel") == "WARN"),
        "crash": bool(crash),
        "minecraft": metadata.get("minecraft"),
        "loader": metadata.get("loader"),
        "loader_version": metadata.get("loader_version"),
        "java": metadata.get("java"),
        "mods_detected": len(mods),
    }

def analizar_excepciones(problemas):
    datos = {}
    for problema in problemas:
        for nombre in problema["excepciones"]:
            item = datos.setdefault(nombre, {"nombre": nombre, "ocurrencias": 0, "problemas": []})
            item["ocurrencias"] += problema.get("ocurrencias", 1)
            if problema.get("tipo") not in item["problemas"]:
                item["problemas"].append(problema.get("tipo"))
    return list(datos.values())

def detectar_crash(lineas):
    """Return True only for strong crash-report markers, not generic errors/chat text."""
    crash_pattern = REGLAS_COMPILADAS["CRASH"]
    for linea in lineas:
        if crash_pattern.search(linea):
            return True
    return False


def calcular_estadisticas(problemas):
    return {
        "problemas": len(problemas),
        "errores": sum(p["ocurrencias"] for p in problemas if p["nivel"] in {"ERROR", "FATAL"}),
        "warnings": sum(p["ocurrencias"] for p in problemas if p["nivel"] == "WARN")
    }

def _extraer_metadata_y_mods(lineas):
    metadata = {
        "minecraft": None,
        "loader": None,
        "loader_version": None,
        "java": None,
        "mods": 0,
    }

    mods = []
    forge_mods = []
    vistos = set()
    forge_vistos = set()
    patterns = (
        re.compile(r"^\s*[-*]\s+([A-Za-z0-9_.-]{2,80})\s+([^\s]+)", re.I),
        re.compile(r"^\s*([A-Za-z0-9_.-]{2,80})\s*\|\s*([^\s|]+)", re.I),
        re.compile(r"^\s*([A-Za-z0-9_.-]{2,80})\s+([0-9][^\s]*)\s*$", re.I),
        re.compile(r"^\s*([A-Za-z0-9_.-]{2,80})\s+([0-9][^\s]*)\s+\(", re.I),
    )
    in_mod_section = False

    for linea in lineas:
        if metadata["minecraft"] is None:
            metadata["minecraft"] = _primero(
                (PATRON_MINECRAFT, PATRON_MINECRAFT_FALLBACK),
                linea,
            )

        if metadata["loader_version"] is None:
            for patron, nombre in (
                (PATRON_NEOFORGE, "NeoForge"),
                (PATRON_FORGE_LOADING, "Forge"),
                (PATRON_FABRIC, "Fabric Loader"),
            ):
                match = patron.search(linea)
                if match:
                    metadata["loader"] = nombre
                    metadata["loader_version"] = match.group(1)
                    break

        if metadata["java"] is None:
            match = PATRON_JAVA_LINE.search(linea)
            if not match:
                match = PATRON_JVM_VERSION.search(linea)
            if not match:
                match = PATRON_JAVA_SIMPLE.search(linea)
            if match:
                metadata["java"] = match.group(1)

        if not metadata["mods"]:
            match = PATRON_MOD_COUNT.search(linea)
            if match:
                metadata["mods"] = int(match.group(1))

        low = linea.lower()

        forge_mod = PATRON_FORGE_MOD_FILE.search(linea)
        if forge_mod:
            _add_mod(
                forge_mods,
                forge_vistos,
                forge_mod.group(1),
                "unknown",
            )

        if PATRON_MOD_SECTION.search(low):
            in_mod_section = True

        if in_mod_section:
            for patron in patterns:
                match = patron.match(linea)
                if match:
                    _add_mod(
                        mods,
                        vistos,
                        match.group(1),
                        match.group(2),
                    )
                    break

        if (
            in_mod_section
            and PATRON_TIMESTAMP.search(linea)
            and not PATRON_MOD_SECTION.search(low)
            and mods
        ):
            in_mod_section = False

    if not mods and forge_mods:
        mods = forge_mods
        vistos = {mod["id"].lower() for mod in mods}

    if not mods:
        for linea in lineas:
            match = PATRON_MOD_FALLBACK.search(linea)
            if (
                match
                and match.group(1).lower()
                not in {"file", "mod", "plugin", "from", "for", "the"}
            ):
                _add_mod(mods, vistos, match.group(1), "unknown")

    if not metadata["mods"]:
        metadata["mods"] = len(mods)

    return metadata, mods


def analizar_log(ruta, progress_callback=None):
    ruta = Path(ruta)

    if not ruta.exists():
        raise FileNotFoundError(f"File not found: {ruta}")

    if not ruta.is_file():
        raise ValueError(f"Path is not a file: {ruta}")

    if progress_callback:
        progress_callback(5, "Reading log file")

    with ruta.open(
        "r",
        encoding="utf-8-sig",
        errors="replace",
    ) as archivo:
        lineas = archivo.readlines()

    if progress_callback:
        progress_callback(15, "Extracting metadata and mods")

    metadata, mods = _extraer_metadata_y_mods(lineas)

    if progress_callback:
        progress_callback(25, "Preparing analysis")

    originales = analizar_problemas(
        lineas,
        mods,
        progress_callback,
    )

    if progress_callback:
        progress_callback(88, "Checking crash information")

    crash = detectar_crash(lineas)

    if crash:
        crash_problem = _crash_report_problem(
            lineas,
            mods,
        )
        if crash_problem:
            originales = [
                problem
                for problem in originales
                if problem.get("tipo") != "CRASH"
            ]
            originales.insert(0, crash_problem)

    if progress_callback:
        progress_callback(93, "Grouping detected problems")

    problemas = agrupar_problemas(originales)
    root_cause = enrich_root_causes(problemas)

    if progress_callback:
        progress_callback(97, "Building statistics")

    resultado = {
        "metadata": metadata,
        "mods": mods,
        "problemas": problemas,
        "errores": [
            p for p in problemas
            if p["nivel"] in {"ERROR", "FATAL"}
        ],
        "warnings": [
            p for p in problemas
            if p["nivel"] == "WARN"
        ],
        "excepciones": analizar_excepciones(originales),
        "crash": crash,
        "crash_confidence": "HIGH" if crash else "NONE",
        "crash_evidence": [
            evidence
            for problem in problemas if problem.get("tipo") == "CRASH"
            for evidence in problem.get("evidence", [])
        ][:8],
        "estadisticas": calcular_estadisticas(problemas),
        "analysis_summary": build_analysis_summary(metadata, mods, problemas, crash),
        "root_cause": root_cause,
    }

    if progress_callback:
        progress_callback(100, "Analysis complete")

    return resultado
