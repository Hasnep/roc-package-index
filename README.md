# Roc Package Index Data

Data for an **unofficial** index of Roc packages, automatically updated weekly.

## Contributing

To contribute a package, add an entry to `data/packages.json`.

```json
"<package-id>": {
  "documentation": "<...>",
  "homepage": "<...>",
  "source_code": ...
}
```

The `source_code` key points to where the package can be downloaded from.

If the package is hosted on GitHub and has releases, set `type` to `"github"` and fill in the `owner` and `repo` fields.

```json
{
  "owner": "<github-username>",
  "repo": "<name-of-repo>",
  "type": "github"
}
```

If the package is hosted on another Git forge, set the `type` to `"git"`, add the URI that the repo can be cloned from and specify the entrypoint file of the package, relative to the root of the repo.

```json
{
  "entrypoint": "src/main.roc",
  "uri": "<...>",
  "type": "git"
}
```

If the package can be downloaded from a URL, set the `type` to `"url"`.

```json
{
  "url": "<...>",
  "type": "url"
}
```
