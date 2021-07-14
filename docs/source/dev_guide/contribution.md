# Contribution Guidelines

Please see [QHub Contribution Guidelines](https://github.com/Quansight/qhub/CONTRIBUTING.md)

# Additions

## Adding new Integration and Features to Qhub

The preferred way to add new features/integrations to the
`qhub-config.yaml` is via a new key as a namespace. If the new
integration requires multiple `images` then use `images` otherwise use
`image`. Additionally `enabled` key determines is the feature is
enabled or disabled. Ensure that the configuration options are in
[qhub/schema.py](https://github.com/Quansight/qhub/blob/main/qhub/schema.py). Additionally
the configuration documentation in Qhub must reflect the
configuration. At a minimum the new feature should also be detailed in
the administration guide and user guide.

```yaml
<feature-key>:
  enabled: true
  image: <image-name>:<image-tag>
  images:
    <image-a>: <image-name>:<image-tag>
    <image-b>: <image-name>:<image-tag>
    ...
```

