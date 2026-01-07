# Cocos Creator Reverse Engineering Tool - AI Coding Guidelines

## Project Overview
This is a reverse engineering tool that converts Cocos Creator Web compiled JavaScript bundles back into editable Cocos Creator projects. It analyzes compiled JS code, extracts cc.Class component definitions, and generates TypeScript scripts with proper project structure.

**Architecture**: Multi-language pipeline (Python core + Node.js analysis + TypeScript generation)
**Supported Versions**: Cocos Creator 2.3.x and 2.4.x
**Key Flow**: JS Analysis → JSON Intermediates → TypeScript Generation → Project Assembly

## Core Components

### Main Entry Point
- `main/main.py`: CLI interface using Click, handles argument parsing and orchestration
- `main/core/reverseEngine.py`: Main engine coordinating the entire reverse process

### Code Analysis Pipeline
- `code_reverse/js_analyzer/parse_bundle.js`: Node.js AST parser for Webpack bundles
- `code_reverse/py_generator/gen_ts.py`: TypeScript code generator from JSON intermediates
- `code_reverse/__init__.py`: CodeReverse class coordinating analysis and generation

### Resource Processing
- `resources_reverse/resourceProcessor.py`: Handles assets, textures, audio, animations
- `main/core/projectGenerator.py`: Creates Cocos Creator project structure and .meta files

## Key Patterns & Conventions

### Global State Management
Use global variables for configuration across modules:
```python
global_config = loadConfig()
global_verbose = False
global_cocosVersion = ""
global_settings = {}
global_paths = {}
```

### Path Handling
Extensive path resolution for different Cocos Creator versions:
```python
possible_paths = [
    os.path.join(source_path, js_file),
    os.path.join(source_path, 'src', js_file),
    os.path.join(source_path, js_file.replace('assets/', '')),
    os.path.join(source_path, 'src', js_file.replace('assets/', ''))
]
```

### Console Output
Use Rich library with custom theme for consistent logging:
```python
console = Console(theme=custom_theme)
logger()["info"]("message")
logger()["success"]("completed")
logger()["error"]("failed")
```

### JSON Intermediates
Analysis generates JSON files that feed into code generation:
- JS analyzer outputs structured JSON representations
- TS generator consumes JSON to create .ts files
- Preserves component hierarchies and dependencies

## Development Workflows

### Running the Tool
```bash
# Basic usage
python -m main.main --path <cocos_web_project> --output <output_dir>

# With bundle filtering
python -m main.main --path <source> --output <output> --bundle-filter fhpoker

# Version-specific processing
python -m main.main --path <source> --output <output> --version-hint 2.4.x
```

### Testing
Extensive test suite in `debug/` directory:
- `test_integration.py`: Creates mock Cocos projects for testing
- Individual component tests for analyzers, generators, processors
- Run with: `python -m pytest debug/`

### Adding New Features
1. Extend `reverseEngine.py` for new processing steps
2. Add analysis logic to `js_analyzer/parse_bundle.js` for new JS patterns
3. Update `gen_ts.py` for new TypeScript generation features
4. Add resource handling in `resourceProcessor.py`

## File Organization
- `main/core/`: Core business logic
- `code_reverse/`: Code analysis and generation
- `resources_reverse/`: Asset processing
- `tools/`: Utility scripts
- `debug/`: Test files and integration setups
- `output/`: Generated project examples

## Dependencies
**Python**: click, rich, esprima, regex, pathlib, json5
**Node.js**: @babel/parser, @babel/traverse, prettier, esprima, fs-extra

## Common Patterns
- Extensive use of glob patterns for file discovery
- Multiple encoding attempts for project files (utf-8, gbk, gb2312, latin-1)
- Webpack bundle detection via signature patterns
- cc.Class component extraction from AST
- Automatic .meta file generation for assets