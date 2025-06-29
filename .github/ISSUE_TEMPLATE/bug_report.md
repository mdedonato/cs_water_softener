---
name: Bug report
about: Create a report to help us improve
title: ''
labels: ''
assignees: ''

---

**Describe the bug**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected behavior**
A clear and concise description of what you expected to happen.

**Screenshots**
If applicable, add screenshots to help explain your problem.

**Environment (please complete the following information):**
 - Home Assistant version: [e.g. 2023.8.0]
 - Integration version: [e.g. 1.0.0]
 - Device: [e.g. Chandler CS_Meter_Soft]
 - OS: [e.g. Home Assistant OS, Docker, etc.]

**Logs**
Please include relevant logs from Home Assistant. You can enable debug logging by adding this to your `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.chandler_water_softener: debug
    bleak: debug
```

**Additional context**
Add any other context about the problem here. 