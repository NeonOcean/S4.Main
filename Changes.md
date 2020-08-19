## v2.1.0 (August 19, 2020)

### Changes
- The next and current version is now listed in mod update notifications.
- Improved promotion capabilities.

### Fixed bugs
- Object interaction registration now differentiates regular toilets from toilet stalls, as regular toilet interactions do not work on toilet stalls.

______________________________

## v2.0.5 (July 16, 2020)

### Fixed bugs
- Fixed bug that caused the mod to fail because it couldn't find the sims 4 folder when using certain languages.

______________________________


## v2.0.4 (July 5, 2020)

### Mod Support
- Using MCCC's auto save feature no longer breaks save files created by Main.
- WickedWhims no longer causes interactions registered with Main to not appear on objects unless they are re-bought.

______________________________

## v2.0.3 (July 2, 2020)

### Saving Sections
- It is now possible to check if a branch or value of a branch exists without getting the value.

### Fixed bugs
- It is now possible to show settings dialogs for branched settings (Such as sim specific settings).

______________________________

## v2.0.2 (June 24, 2020)

### Fixed bugs
- Fixed a critical bug for mac computers - We can now correctly find the mods folder.

______________________________

## v2.0.1 (June 24, 2020)

### Fixed bugs
- Fixed announcer priorities.

______________________________

## v2.0.0 (June 19, 2020)

### Mod Information Files
- Mod information file names no longer need to start with 'NeonOcean-Mod' it just needs to contain it.
- Version numbers now follow the semantic versioning specification. https://semver.org/
- Changed the format of the 'Distribution' value in mod information files.

### New Features
- Added new event system.
- Added new object saving system.
- A new debug interaction allows users to load specific mod save folders, in the event an incorrect one is loaded.
- Added in-game notifications to warn players when any mod save does not match the game's save.
- Settings are now listed in dialog instead of an interaction menu.
- Created settings list dialog framework which this mod moved over to using.
- Users can now be notified of mod updates without requiring the creation of python code.

### Changes
- Changed this mod's namespace from NeonOcean.Main to NeonOcean.S4.Main.
- Saving objects can no longer register themselves to a saving object handler, it should now be done manually.
- Saving objects now take the save file paths as parameters for loading and saving methods instead of save slot ids.
- Improved new debug logging to prevent the build up of large log files.
- Added icons to some mod interactions and interaction categories.
- Only one update notification is now shown for all outdated mods, users can select mod websites to visit from a picker dialog.
- Reworked the interaction object registration system, it now supports different object interactions lists.

### Fixed bugs
- Persistence objects for saving sections no longer break when loading non existent data in the saving section.
- The built in saving handler now correctly logs and warns the player about save failures.
- Mod save backups will now correctly follow their tied game backups when overriding a save.
- \_\_init\_\_ modules are now correctly handled by the loading system.
- Fixed mod documentation links.
- Patched functions and methods will now return a value when patched in the custom or replace modes.
- Main will no longer incorrectly warn about python-less mods not being loaded.
- Mods without a load order file will now still load even if the mod Order is installed.

______________________________

## v1.3.0 (July 15, 2019)
### New Features
- New systems now allow for the saving of data that is tied to a Sims 4 save file.
- The director's announcer now has a bunch more announcement capabilities.  
- It is now possible to patch a function directly, meaning can you input the original and target callables and receive the patch as the output.
- The interaction object registration system now supports the ability to determine what each object is and should run much faster.
- Mod information files now allow for specification of version display strings. These are only used for display, this will not allow for an internal version number outside the standard Major.Minor.Patch.Build format.
- The distribution system now also supports version display strings, these will be shown on mod update notifications as the next version number if the value exists.


### Changes
- All of Main's interactions will now only show up when clicking on Sims instead of everything.
- Changed the way persistent files are formatted, this will likely cause settings to reset.
- The persistent class changed to become more extendable, you will also now need to specify the class as "PersistentFile" instead of just "Persistent" to save data to a file.
- Made distribution system's version and promotion file reading is more forgiving; if sections of the files cannot be read they will be ignored instead.
- Setting dialogs now take setting wrapper objects instead of the setting directly.
- ####Mod Information Files
	- The values "Rating", "ScriptPaths", "Requirements" and "Compatibility" in the mod file's root are no longer required to exist.
	- 'ScriptPaths' values can now be dictionaries along with strings. Using a dictionary will allow you to specify the root of the script path. Check the documentation for details, if the page exists yet.

### Fixed bugs
- Patching now correctly preserves the original callable's parameters. Previously, in certain cases such as using the "getfullargspec" function in the inspect module, it would incorrectly show the wrapper's parameters instead of the original's.
- Modules named \_\_init\_\_ are no longer imported twice.

______________________________

## v1.2.0 (June 12, 2019)
### New Features
- The distribution system is now available as a tool instead being only usable by this mod.
- Completely reworked setting dialogs system to be far more versatile.
- Changed settings related to the distribution system to allow users to disable update checking for individual mods.

### Changes
- The debug system now logs exceptions automatically without their required input.
- Added an icon to the root NeonOcean pie menu category.
- Changed this mod's license to CC BY, this change was mostly intended to make the parts of this mod available for reuse in other creator's projects.
- ####Mod Information Files
	- Mod information files can now be prefixed with "NeonOcean-Mod" instead of having a forced, uniform name.
	- Multiple word keys in the mod file no longer use spaces between the words.
	- The "LoadController" value is now optional, not including it is a much better way of telling Main you don't want it to load the mod, opposed to the old option of leaving it blank.
	- "Distribution" is optional as well, not including it signal distributions systems to not check for the mod's updates, it will also not appear in Main's settings meant to enable or disable the update checking.
	- The "LowestVersion" and "HighestVersion" values in mod compatibility data are also, now optional.

### Fixed Bugs
- Mods are now correctly loaded without the mod Order by NeonOcean being installed.
- Fixed problem where NeonOcean update notifications sent users to the mod's documentation page instead the mod page.
- The notification showing that some mods have compatibility problems now correctly lists the mods in question.
- Invalid setting input notifications now correctly display mod name and input information.
- The timer tool no longer erroneously warns of oversleep when changing from a high interval to a low interval while the timer is running. 
- Debug session files now display certain information correctly.
- Fixed potential bugs in the debug system related to threads.
- Debug write failure notifications now correctly display the error information.

______________________________

## v1.1.0 (March 26, 2019)
During the development of this version I realized that it might be a good idea to open this mod up from being a toolkit for just my mods, to being a toolkit for potentially many mods. Some of the largest changes made reflect this.
 
- The names and paths of mods supposed to be loaded by Main are no longer hard coded, it will instead look through the mod folder for supporting mods.
- Mod information is now stored in a single JSON file, These files are also required for Main to detect or load the mod.
- A new system for handling settings is now in place.	
- Added tools for interactions, for example, interactions using Main can specify which objects they would like to be available on through tuning.
- New tools for in-game settings dialogs now allow a mod's settings to be changed far more easily.
- In-game notifications will now appear telling you when an update is available or to display promotions from NeonOcean.
- Interactions now exist that can direct you to web pages relevant to this mod, such as the documentation.
- Addition and removal of this mod are can now be facilitated through an installer or uninstaller. These currently are only usable on windows computers.

______________________________

## v1.0.0 (July 26, 2018)
 - Initial release