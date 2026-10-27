# Launcher instance guard

A session-local named mutex prevents a second launcher UI or setup window. The second process displays an instruction to close the existing launcher and exits with code 2. The original launcher continues running. A crashed owner's abandoned mutex can be acquired on restart.

Read-only snapshot commands and the executable preparation helper bypass the UI guard. Closing the launcher does not terminate the game.

Validation: launcher build and process-level checks for duplicate prompt/exit code, original survival, and successful reopening after close. The existing unrelated CS1690 build warning remains.
