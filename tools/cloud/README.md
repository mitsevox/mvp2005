# Running this project in a cloud session

Everything the agents use is in the repo, except the game's `main.dol`, which never goes in git. A
cloud session gets it from the same private build container CI uses (`mitsevox/mvp2005-build`,
image `ghcr.io/mitsevox/mvp2005-build:main`), with a read-only token the owner creates.

## Owner: one-time (the session never sees the token's value)

1. Build container: a **private** repo `mitsevox/mvp2005-build`, made like `mitsevox/tw2004-build`
   (its Dockerfile and publish workflow), holding only `orig/<VERSION>/sys/main.dol`. In the
   package's settings, "Manage Actions access", give `mitsevox/mvp2005` Read access so CI can pull it.
2. GitHub -> Settings -> Developer settings -> Personal access tokens -> Tokens (classic) ->
   Generate new token (classic). Scope: `read:packages` only. Give it an expiry you are happy with.
3. In the cloud environment's settings (claude.ai/code -> the environment for this repo ->
   environment variables / secrets), add `MVP_BUILD_TOKEN` = that token.

## Session: setup

```
bash tools/cloud/setup.sh      # main.dol, compilers (wibo), permuter + m2c beside the repo, build
```
It must end with `build/<VERSION>/main.dol: OK`.

Pitfall met on tw2004: when the build repo is created from its template, the template's first
container build can finish after the commit that adds `main.dol` and overwrite `:main` with an empty
image ("main.dol not found"): re-run the latest container build.
