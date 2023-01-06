# CHANGELOG

## [0.2.0] - 2023-01
Basic mapping and gridding.

## [0.1.0] - 2023-01-04
First functional release. Provides users with a basic interface for accessing scans from a local catalog.
### Added
- The `Catalog` class, complete with functions to both filter and return scans from a local Bluesky catalog. This class also provides access to the raw Bluesky catalog through the `bs_catalog` class variable. 
- The `Scan` class, which provides easy-to-access metadata values and the raw Bluesky run (`bs_run`) associated with the scan.
### Notes
- v0.1.0 assumes that a catalog has already been unpacked and provided a name for local usage. The unpacking step will be addressed in future releases.
- A demo of v0.1.0's features can be found in the notebook `demos/xiu-demo-0-1-0.ipynb`.