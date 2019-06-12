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