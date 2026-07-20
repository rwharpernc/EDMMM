# Changelog

All notable changes to this project are documented here. Format loosely
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions
match `EDMMM/version` and the git tag each release is built from.

## [Unreleased]

### Changed

- Renamed the project from **EDMMT** ("Elite Dangerous Modern Massacre
  Tracker") to **EDMMM** ("Elite Dangerous: My Mission Manager"), including
  the plugin folder name, the `edmmm` Python package (was `edmmt`), the log
  file name (`EDMMM.log`), and all in-app labels.
  - **Upgrade note:** because plugin settings and the log file are
    namespaced by the plugin's folder name, upgrading from an `EDMMT`-named
    install to `EDMMM` resets display settings to their defaults once. Kill
    and mission tracking are unaffected — that state is rebuilt from the
    journal on startup regardless of plugin folder name.
- Removed the standalone `EDMC-Massacres` reference project that used to
  live alongside this one; it was only ever kept for reference and has no
  bearing on EDMMM's code.

## [1.2.0] and earlier

Released under the EDMMT name, prior to this changelog's introduction.
