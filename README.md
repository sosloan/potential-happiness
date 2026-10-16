# jq playground

A small local web app for trying [jq](https://jqlang.github.io/jq/) queries against JSON.
The browser interface is served locally, and query input is passed directly to the installed
`jq` executable without invoking a shell.

## Requirements

- Python 3.9 or newer
- jq installed and available on your `PATH`

## Run

```sh
python3 app.py
```

Open <http://127.0.0.1:8000>. Set the `PORT` environment variable to use a different port.
The server binds to localhost and does not send your JSON to an external service.

Press **Run query** or use **Ctrl/⌘ + Enter**. The sample button restores the example document
and query. Queries run with a five-second timeout.

## Test

```sh
python3 -m unittest discover -s tests
```