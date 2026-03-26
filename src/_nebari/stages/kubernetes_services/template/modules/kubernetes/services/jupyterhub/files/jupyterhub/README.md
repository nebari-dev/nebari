# JupyterHub Profile Configuration

This directory contains JupyterHub configuration files that customize user pod specifications through KubeSpawner.

## Configuration Flow

Configuration flows through multiple layers:

```
Helm values.yaml
       ↓
Z2JH jupyterhub_config.py (sets c.KubeSpawner.* traitlets)
       ↓
Nebari 03-profiles.py (modifies via kubespawner_override)
       ↓
KubeSpawner._apply_overrides() (applies kubespawner_override to spawner)
       ↓
KubeSpawner makes pod spec (calls objects.make_pod())
       ↓
objects.make_pod() applies extra_pod_config/extra_container_config (REPLACES)
       ↓
Final K8s Pod Spec
```

## Key Concepts

### Template String Expansion

KubeSpawner supports template strings like `{username}`, `{user_server}`, and `{pvc_name}` that get expanded at pod creation time.

**CRITICAL**: Only certain configuration paths get template expansion:

| Config Path | Template Expansion | Notes |
|-------------|-------------------|-------|
| `volume_mounts` (traitlet) | ✅ YES | Use this for mounts needing templates |
| `volumes` (traitlet) | ✅ YES | Use this for volumes needing templates |
| `extra_container_config["volumeMounts"]` | ❌ NO | Goes through `update_k8s_model()` which skips expansion |
| `extra_pod_config["volumes"]` | ❌ NO | Goes through `update_k8s_model()` which skips expansion |

### Correct Pattern for Volume Mounts

```python
# CORRECT: Use volume_mounts dict - gets template expansion
def my_profile_function():
    return {
        "volumes": {
            "my-volume": {
                "name": "volume-{user_server}",
                "persistentVolumeClaim": {"claimName": "{pvc_name}"},
            },
        },
        "volume_mounts": {
            "my-mount": {
                "mountPath": "/home/{username}",
                "name": "volume-{user_server}",
            },
        },
    }
```

```python
# WRONG: extra_container_config does NOT get template expansion
def my_profile_function():
    return {
        "extra_container_config": {
            "volumeMounts": [
                {
                    "mountPath": "/home/{username}",  # Will NOT expand!
                    "name": "volume-{user_server}",   # Will NOT expand!
                },
            ],
        },
    }
```

### How deep_merge Works

The `deep_merge()` function in `03-profiles.py` combines configurations from multiple profile functions:

- **Dicts**: Merged recursively by key
- **Lists**: Concatenated (not deduplicated)
- **Scalars**: Left value wins

This means:
- Using the same dict key in `volumes` will merge/override
- Using different dict keys will result in separate entries
- List items (like `init_containers`) accumulate

## Profile Functions

Each profile function returns a dict with these possible keys:

```python
{
    "volumes": {},              # Pod volumes (dict for merging)
    "volume_mounts": {},        # Container volume mounts (dict for merging)
    "extra_pod_config": {},     # Raw pod spec additions (REPLACES, no template expansion)
    "extra_container_config": {},  # Raw container spec additions (REPLACES, no template expansion)
    "init_containers": [],      # Init containers (list, gets concatenated)
    "environment": {},          # Environment variables
    "lifecycle_hooks": {},      # Container lifecycle hooks
}
```

## Files

- `03-profiles.py` - Main profile configuration logic
- `04-auth.py` - Authentication configuration
- `05-dask.py` - Dask gateway configuration
