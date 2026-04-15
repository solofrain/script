# Auto Rebuild on Source File Changes

The two scripts monitors file changes, rebuild EPICS module and corresponding IOC, and restart the IOC.

To achieve restart, the IOC is expected to be restarted if the current process is killed, e.g.,

```
while true; do
    ./st.cmd
done
```

The example in the scripts is `ADGermanium`.

- `auto-update-from-github.sh`

Monitors Github repo.

Generic inotify + GitHub polling build watcher.
- Polls a GitHub branch and pulls when upstream changes
- Watches local directories for file changes via inotify
- Coalesces bursts of events so one save => one build
- Serializes builds with a lock
- Rebuilds both the module and the IOC on any change

- `auto-update-binary.sh`

Monitors local file changes.

Continuously monitor the changes to local files, and on changes:
- Rebuilds both the module and the IOC
- Kill the IOC if the build succeeds or if not rebuilt (uses `pkill -f germaniumDetector.*st\.cmd`)
