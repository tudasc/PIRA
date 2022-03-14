find . -iname "*.json" -exec python -m json.tool --sort-keys --indent 2 {} {} \;
