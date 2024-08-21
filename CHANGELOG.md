# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [Unreleased]


## [0.1.0] - 2024-08-21

### Added
- More details in some error messages.

### Changed
- Make less assumptions when reading faction variant list. Now captures everything between '[' and ']', and parses it. No longer relies on the list being in a single line.
- Ignore faction variants serving as separators (starting with '-').
- Ignore comment lines in faction variant lists.
- Ignore comments when interpreting motorpools as JSON code.
- Try multiple file names with different combinations of upper- and lower-case name parts when looking for motorpool files.

### Fixed
- Some typos in the code.


## [0.2.0] - 2023-12-23

### Added
- Faction database generation ability.

### Changed
- Removed support for writing JSON content directly to the standard output.
