# Contributing

Contributions are welcome.

Before submitting a change:

```bash
python3 -m compileall -q lbm_vdrc
python3 -m unittest discover -s tests -v
bash -n install.sh
bash -n uninstall.sh
```

Please preserve these design rules:

- do not hide destructive actions;
- keep the source VM by default during migration work;
- preserve ANSI right-border alignment;
- do not print stored secrets;
- prefer native hypervisor backup mechanisms when they are safer;
- document any new privilege or dependency;
- add or update tests for UI rendering and parsers.

Designed & Developed by **antonios.mortos@outlook.com**
