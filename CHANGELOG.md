# Enhances project setup, standardizes formatting, and refines CI/CD and dependency management

This comprehensive update introduces consistent code style via EditorConfig, streamlines development environment setup with a new script, and transitions dependency resolution to `uv` for reproducible builds. It also significantly refactors the installation script for robustness and updates testing workflows and documentation.

## Changes

- **Configuration & Standards:** Introduced `.editorconfig`, `.gitattributes`, `.kateconfig`, and `.shellcheckrc` files to enforce consistent code style, line endings, and editor settings across various programming languages and file types.
- **Dependency Management:** Migrated Python dependency resolution to `uv`, introducing `uv.lock` for reproducible builds and updating `requirements.txt` with version-specific dependencies for `numpy`, `matplotlib`, and `scipy`. System-level dependencies for Debian and Arch Linux were also expanded.
- **Build & CI/CD:** Modified `.github/workflows/test.yml` to include new Klipper repositories (`KalicoCrew/kalico`), expanded Python test matrix to include `3.13`, updated GitHub Actions versions to v6, and refined build dependencies.
- **Installation Script (`install.sh`):** Enhanced robustness with OS checks, added user confirmation, updated system package installation, switched to `uv pip sync` for Python dependencies, and now uses specific "punisher_data" paths for Klipper components.
- **Project Metadata:** Updated `pyproject.toml` to reflect new author information and project URLs, and added core dependencies.
- **Code Quality:** Applied extensive type hinting refinements (`List` to `list`, `Dict` to `dict`, `Tuple` to `tuple`) and removed old copyright headers across Python source files.
- **Documentation:** Updated `README.md` and `.github/ISSUE_TEMPLATE/config.yml` to point to a new Wiki and Telegram group for support.
- **New Feature:** Added `exa_agent.py` as a new script for running an Exa agent in streaming mode.
- **Internal Logic:** Adjusted Klipper virtual environment path handling, updated Moonraker `update_manager` to reference `uv.lock`, and refined error handling and process priority management in `shaketune_process.py`.
- **Cleanup:** Removed `.git-blame-ignore-revs` and `.github/FUNDING.yml`, and significantly refined `.gitignore` patterns.

### Impact

- **Behavioral Changes:** The `install.sh` script now requires user confirmation and uses hardcoded paths (`punisher_data`) for Klipper components, which might require adjustments for users with different setups. Python dependency installation will now leverage `uv` (if available in the environment) leading to potentially faster and more reliable installs.
- **Dependencies Affected:** Core Python dependencies (GitPython, NumPy, Zstandard) are now strictly pinned across different Python versions via `uv.lock`. New system packages are required for a complete setup.
- **Breaking Changes:** Hardcoded paths in `install.sh` could be considered a breaking change for existing non-"punisher_data" setups. The update_manager configuration in `moonraker.conf` now expects `uv.lock` as the requirements file.
- **Performance Implications:** Reduced process priority for Shake&Tune computations aims to mitigate performance impact on the main Klipper process. The introduction of `uv` for dependency management may improve installation speed.
