# 7. Riferimento completo delle funzioni

Questo capitolo riporta tutte le funzioni top-level dei due script con posizione, firma e implementazione esatta dello snapshot. La spiegazione del flusso e delle implicazioni si trova nei capitoli 2–6. I riferimenti di riga valgono per i file originali inclusi.

## generate_simulations.py

| Funzione | Riga | Firma |
|---|---|---|
| `_yaml_rt` | 74 | `` |
| `load_template` | 81 | `template_path: Path` |
| `dump_yaml` | 90 | `config: CommentedMap, out_path: Path` |
| `make_wind_speeds` | 101 | `rng_np: np.random.Generator, rng_py: random.Random` |
| `make_wind_dirs` | 117 | `rng_py: random.Random` |
| `all_combinations` | 128 | `grid: ParamGrid` |
| `generate_configs` | 141 | `template: CommentedMap, out_dir: Path, n: int, grid: ParamGrid, seed: int | None, prefix: str='config'` |
| `run_specula` | 198 | `config_path: Path, log_path: Path, *, specula_exe: str='specula', cwd: Path | None=None` |
| `dir_has_anything` | 230 | `path: Path` |
| `wipe_run_outputs` | 241 | `*paths: Path` |
| `main` | 253 | `` |

### `_yaml_rt`

File: [generate_simulations.py](../generate_simulations.py), righe 74–78.

```python
def _yaml_rt() -> YAML:
    y = YAML()
    y.preserve_quotes = True
    y.indent(mapping=2, sequence=4, offset=2)
    return y
```


### `load_template`

File: [generate_simulations.py](../generate_simulations.py), righe 81–87.

```python
def load_template(template_path: Path) -> CommentedMap:
    y = _yaml_rt()
    with template_path.open("r", encoding="utf-8") as f:
        template = y.load(f)
    if template is None:
        raise RuntimeError(f"Template vuoto o non valido: {template_path}")
    return template
```


### `dump_yaml`

File: [generate_simulations.py](../generate_simulations.py), righe 90–94.

```python
def dump_yaml(config: CommentedMap, out_path: Path) -> None:
    y = _yaml_rt()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        y.dump(config, f)
```


### `make_wind_speeds`

File: [generate_simulations.py](../generate_simulations.py), righe 101–114.

```python
def make_wind_speeds(rng_np: np.random.Generator, rng_py: random.Random) -> CommentedSeq:
    speeds = []
    for _ in range(30):
        v = rng_np.poisson(lam=5) + rng_py.uniform(0, 1)
        v = min(max(v, 5), 20)
        speeds.append(round(v, 1))
    for _ in range(5):
        v = rng_np.poisson(lam=5) + rng_py.uniform(2, 3)
        v = min(max(v, 5), 20)
        speeds.append(round(v, 1))

    seq = CommentedSeq(speeds)
    seq.fa.set_flow_style()
    return seq
```


### `make_wind_dirs`

File: [generate_simulations.py](../generate_simulations.py), righe 117–121.

```python
def make_wind_dirs(rng_py: random.Random) -> CommentedSeq:
    dirs = [rng_py.choice([0, 90, -90, 180, -180]) for _ in range(35)]
    seq = CommentedSeq(dirs)
    seq.fa.set_flow_style()
    return seq
```


### `all_combinations`

File: [generate_simulations.py](../generate_simulations.py), righe 128–138.

```python
def all_combinations(grid: ParamGrid) -> List[Tuple[int, float, int, int, int]]:
    """
    (zenith_angle, seeing, mag, L0, nmodes)
    """
    return list(itertools.product(
        grid.zenith_angles,
        grid.seeings,
        grid.mags,
        grid.L0s,
        grid.nmodes_list
    ))
```


### `generate_configs`

File: [generate_simulations.py](../generate_simulations.py), righe 141–191.

```python
def generate_configs(
    template: CommentedMap,
    out_dir: Path,
    n: int,
    grid: ParamGrid,
    seed: int | None,
    prefix: str = "config",
) -> List[Path]:
    rng_py = random.Random(seed)
    rng_np = np.random.default_rng(seed)

    combos = all_combinations(grid)
    if n > len(combos):
        raise ValueError(
            f"Richiesti n={n} ma le combinazioni possibili sono {len(combos)}. "
            f"Riduci n o amplia la griglia."
        )

    chosen = rng_py.sample(combos, n)
    out_dir.mkdir(parents=True, exist_ok=True)

    generated: List[Path] = []
    for i, (za, seeing, mag, l0, nmodes) in enumerate(chosen):
        config = CommentedMap(template)

        # Parametri principali
        config["main"]["zenithAngleInDeg"] = int(za)
        config["seeing"]["constant"] = float(seeing)

        # Vento in flow-style inline
        config["wind_speed"]["constant"] = make_wind_speeds(rng_np, rng_py)
        config["wind_direction"]["constant"] = make_wind_dirs(rng_py)

        # Magnitudini: on-axis == NGS SEMPRE
        config["source_on_axis"]["magnitude"] = int(mag)
        config["source_ngs"]["magnitude"] = int(mag)

        # Altri parametri
        config["atmo"]["L0"] = int(l0)
        config["dm"]["nmodes"] = int(nmodes)

        # Nome file: una sola magnitudine
        filename = (
            f"{prefix}_{i:04d}_"
            f"za{za}_s{seeing}_mag{mag}_L0{l0:03d}_n{nmodes}.yml"
        )
        path = out_dir / filename
        dump_yaml(config, path)
        generated.append(path)

    return generated
```


### `run_specula`

File: [generate_simulations.py](../generate_simulations.py), righe 198–223.

```python
def run_specula(
    config_path: Path,
    log_path: Path,
    *,
    specula_exe: str = "specula",
    cwd: Path | None = None,
) -> int:
    cmd = [specula_exe, str(config_path)]

    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as logf:
        logf.write("\n" + "=" * 120 + "\n")
        logf.write(f"CMD: {' '.join(cmd)}\n")

        proc = subprocess.run(
            cmd,
            cwd=str(cwd) if cwd is not None else None,
            stdout=logf,
            stderr=logf,
            check=False,
            text=True,
            env=os.environ.copy(),
        )
        logf.write(f"\nEXIT CODE: {proc.returncode}\n")

    return int(proc.returncode)
```


### `dir_has_anything`

File: [generate_simulations.py](../generate_simulations.py), righe 230–238.

```python
def dir_has_anything(path: Path) -> bool:
    """True se la directory esiste e contiene almeno un file/cartella."""
    if not path.exists() or not path.is_dir():
        return False
    try:
        next(path.iterdir())
        return True
    except StopIteration:
        return False
```


### `wipe_run_outputs`

File: [generate_simulations.py](../generate_simulations.py), righe 241–246.

```python
def wipe_run_outputs(*paths: Path) -> None:
    """Cancella completamente le directory passate e le ricrea vuote."""
    for p in paths:
        if p.exists():
            shutil.rmtree(p)
        p.mkdir(parents=True, exist_ok=True)
```


### `main`

File: [generate_simulations.py](../generate_simulations.py), righe 253–347.

```python
def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate YAML configs and run SPECULA as: specula <config.yml>"
    )
    parser.add_argument("--n", type=int, default=10, help="Numero di simulazioni/config da generare")
    parser.add_argument("--seed", type=int, default=None, help="Seed per riproducibilità (python + numpy)")
    parser.add_argument("--run-id", type=str, default=None, help="Nome run (default: auto)")
    parser.add_argument("--template", type=str, default="template.yml", help="Path al template YAML (relativo a PROJECT_ROOT)")
    parser.add_argument("--specula-exe", type=str, default="specula", help="Eseguibile specula (default: 'specula')")
    parser.add_argument("--dry-run", action="store_true", help="Genera solo YAML, non lancia specula")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent

    template_path = (project_root / args.template).resolve()
    if not template_path.is_file():
        print(f"[ERROR] template non trovato: {template_path}")
        return 2

    # Run ID
    if args.run_id:
        run_id = args.run_id
    else:
        if args.seed is not None:
            run_id = f"run_seed{args.seed}_n{args.n}"
        else:
            run_id = f"run_{random.Random().randrange(10**8):08d}_n{args.n}"

    # Output directories (tutti)
    base_data = project_root / "data"
    configs_dir = base_data / "configs"
    logs_dir = base_data / "logs" 
    sims_dir = base_data / "sims"  # output SPECULA (solo se il template lo punta qui)

    # Se esiste QUALSIASI output, cancella TUTTO e riparti
    already_there = (
        dir_has_anything(configs_dir)
        or dir_has_anything(logs_dir)
        or dir_has_anything(sims_dir)
    )

    if already_there:
        print(f"[INFO] Output già presenti per run_id='{run_id}'. Cancello TUTTO (configs/logs/sims) e rigenero.")
        wipe_run_outputs(configs_dir, logs_dir, sims_dir)
    else:
        configs_dir.mkdir(parents=True, exist_ok=True)
        logs_dir.mkdir(parents=True, exist_ok=True)
        sims_dir.mkdir(parents=True, exist_ok=True)

    template = load_template(template_path)

    # Genera configs
    generated = generate_configs(
        template=template,
        out_dir=configs_dir,
        n=args.n,
        grid=DEFAULT_GRID,
        seed=args.seed,
        prefix="config",
    )

    print(f"[INFO] Generati {len(generated)} YAML in: {configs_dir}")
    print(f"[INFO] Logs in: {logs_dir}")
    print(f"[INFO] Sims dir (pulita/creata): {sims_dir}")
    print("")

    if args.dry_run:
        return 0

    # Lancia specula
    n_ok, n_fail = 0, 0
    for cfg in sorted(generated):
        log_path = logs_dir / f"{cfg.stem}.log"
        print(f"[RUN] {args.specula_exe} {cfg.name}")

        code = run_specula(
            config_path=cfg,
            log_path=log_path,
            specula_exe=args.specula_exe,
            cwd=project_root,  # utile se nel YAML ci sono path relativi
        )

        if code == 0:
            n_ok += 1
        else:
            n_fail += 1
            print(f"[WARN] Fallita: {cfg.name} (exit={code}) -> log: {log_path}")

    print("")
    print(f"[DONE] OK={n_ok} FAIL={n_fail}")
    print(f"[DONE] Configs: {configs_dir}")
    print(f"[DONE] Logs:    {logs_dir}")
    print(f"[DONE] Sims:    {sims_dir}")

    return 0 if n_fail == 0 else 1
```

## GANtastic-PSF2.0.py

| Funzione | Riga | Firma |
|---|---|---|
| `should_pause` | 148 | `` |
| `load_state` | 151 | `` |
| `save_state` | 174 | `state: dict` |
| `run_specula_command` | 178 | `` |
| `alpha_for_cycle` | 221 | `cycle_index: int` |
| `_ensure_loss_log_header` | 240 | `path: str` |
| `append_loss_log` | 245 | `path: str, global_epoch: int, cycle_index: int, alpha: float, gen_loss: float, disc_loss: float, val_l1: float` |
| `save_cycle_loss_txt` | 252 | `out_path: str, epochs, gen_losses, disc_losses, val_l1s, cycle_index: int, alpha: float` |
| `save_cycle_loss_png` | 259 | `out_path: str, epochs, gen_losses, disc_losses, val_l1s, cycle_index: int, alpha: float` |
| `try_load_seed_models` | 280 | `input_shape, psf_shape` |
| `adjust_X_to_seed_if_needed` | 315 | `X: np.ndarray` |
| `list_specula_folders` | 389 | `base_dir: str` |
| `crop_center` | 392 | `frame: np.ndarray, size: int=64` |
| `load_data_from_folders` | 398 | `folders, start_frame=50, crop_size=64` |
| `fit_or_load_x_scaler` | 438 | `X_train: np.ndarray` |
| `apply_x_scaler` | 459 | `X: np.ndarray, mu: np.ndarray, sigma: np.ndarray` |
| `normalize_y_per_frame_peak` | 462 | `Y: np.ndarray` |
| `make_datasets_with_norm` | 466 | `X, Y, batch_size=32` |
| `save_val_images` | 501 | `generator, X_val, Y_val, out_dir, epoch, prefix='val', every=2` |
| `build_generator` | 552 | `input_shape` |
| `build_discriminator` | 584 | `psf_shape` |
| `discriminator_loss` | 608 | `real_output, fake_output` |
| `generator_loss` | 612 | `fake_output, generated_image, target_image, lambda_rec, alpha` |
| `train_step` | 623 | `generator, discriminator, telemetry_batch, real_psf_batch, gen_optimizer, disc_optimizer, lambda_rec, alpha` |
| `_handle_sigint` | 653 | `sig, frame` |
| `main` | 662 | `` |

### `should_pause`

File: [GANtastic-PSF2.0.py](../GANtastic-PSF2.0.py), righe 148–149.

```python
def should_pause() -> bool:
    return os.path.exists(PAUSE_FILE)
```


### `load_state`

File: [GANtastic-PSF2.0.py](../GANtastic-PSF2.0.py), righe 151–172.

```python
def load_state():
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH, "r") as f:
            s = json.load(f)
        # backward compatibility
        if "cycle_index" not in s:
            s["cycle_index"] = 0
        if "history" not in s:
            s["history"] = {"gen_loss": [], "disc_loss": [], "val_l1": [], "alpha": [], "cycle": []}
        else:
            s["history"].setdefault("alpha", [])
            s["history"].setdefault("cycle", [])
        return s

    return {
        "used_folders": [],
        "global_epoch": 0,
        "cycle_index": 0,
        "best_val_l1": float("inf"),
        "wait": 0,
        "history": {"gen_loss": [], "disc_loss": [], "val_l1": [], "alpha": [], "cycle": []},
    }
```


### `save_state`

File: [GANtastic-PSF2.0.py](../GANtastic-PSF2.0.py), righe 174–176.

```python
def save_state(state: dict):
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)
```


### `run_specula_command`

File: [GANtastic-PSF2.0.py](../GANtastic-PSF2.0.py), righe 178–215.

```python
def run_specula_command() -> bool:
    if SPECULA_CMD is None or len(SPECULA_CMD) == 0:
        print("[SPECULA] SPECULA_CMD non configurato: salto generazione.")
        return False

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cmd_str = " ".join(SPECULA_CMD)

    print("\n[SPECULA] Launch:", ts)
    print("[SPECULA] CMD:", cmd_str)
    print("[SPECULA] CWD:", SPECULA_WORKDIR)
    print("[SPECULA] LOG:", SPECULA_LOG)

    with open(SPECULA_LOG, "a") as logf:
        logf.write("\n" + "=" * 90 + "\n")
        logf.write(f"[{ts}] Running: {cmd_str}\n")
        logf.flush()
        try:
            res = subprocess.run(
                SPECULA_CMD,
                cwd=SPECULA_WORKDIR,
                stdout=logf,
                stderr=logf,
                check=False,
                text=True,
            )
        except Exception as e:
            logf.write(f"[{ts}] ERROR launching SPECULA: {repr(e)}\n")
            logf.flush()
            print("[SPECULA] ERRORE lancio:", e)
            return False

    if res.returncode != 0:
        print(f"[SPECULA] Terminato con return code {res.returncode} (vedi log).")
        return False

    print("[SPECULA] Terminato correttamente.")
    return True
```


### `alpha_for_cycle`

File: [GANtastic-PSF2.0.py](../GANtastic-PSF2.0.py), righe 221–238.

```python
def alpha_for_cycle(cycle_index: int) -> float:
    """
    Schedule richiesto:
      0 -> 0.5
      1 -> 0.4
      2 -> 0.3
      3 -> 0.4
      4 -> 0.5
      5 -> 0.6
      6 -> 0.7
      >=7 -> 0.7
    """
    pattern = [0.5, 0.4, 0.3, 0.4, 0.5, 0.6, 0.7]
    if cycle_index < 0:
        cycle_index = 0
    if cycle_index >= len(pattern):
        return 0.7
    return float(pattern[cycle_index])
```


### `_ensure_loss_log_header`

File: [GANtastic-PSF2.0.py](../GANtastic-PSF2.0.py), righe 240–243.

```python
def _ensure_loss_log_header(path: str):
    if not os.path.exists(path):
        with open(path, "w") as f:
            f.write("# global_epoch  cycle_index  alpha  gen_loss  disc_loss  val_l1\n")
```


### `append_loss_log`

File: [GANtastic-PSF2.0.py](../GANtastic-PSF2.0.py), righe 245–250.

```python
def append_loss_log(path: str, global_epoch: int, cycle_index: int, alpha: float,
                    gen_loss: float, disc_loss: float, val_l1: float):
    _ensure_loss_log_header(path)
    with open(path, "a") as f:
        f.write(f"{global_epoch:6d}  {cycle_index:4d}  {alpha:0.3f}  "
                f"{gen_loss:0.8e}  {disc_loss:0.8e}  {val_l1:0.8e}\n")
```


### `save_cycle_loss_txt`

File: [GANtastic-PSF2.0.py](../GANtastic-PSF2.0.py), righe 252–257.

```python
def save_cycle_loss_txt(out_path: str, epochs, gen_losses, disc_losses, val_l1s, cycle_index: int, alpha: float):
    with open(out_path, "w") as f:
        f.write("# epoch(global)  cycle_index  alpha  gen_loss  disc_loss  val_l1\n")
        for e, g, d, v in zip(epochs, gen_losses, disc_losses, val_l1s):
            f.write(f"{int(e):6d}  {cycle_index:4d}  {alpha:0.3f}  "
                    f"{float(g):0.8e}  {float(d):0.8e}  {float(v):0.8e}\n")
```


### `save_cycle_loss_png`

File: [GANtastic-PSF2.0.py](../GANtastic-PSF2.0.py), righe 259–274.

```python
def save_cycle_loss_png(out_path: str, epochs, gen_losses, disc_losses, val_l1s, cycle_index: int, alpha: float):
    if len(epochs) == 0:
        return
    fig = plt.figure(figsize=(10, 5))
    ax = fig.add_subplot(1, 1, 1)
    ax.plot(epochs, gen_losses, label="Gen loss")
    ax.plot(epochs, disc_losses, label="Disc loss")
    ax.plot(epochs, val_l1s, label="Val L1")
    ax.set_xlabel("Global epoch")
    ax.set_ylabel("Loss")
    ax.set_title(f"Cycle {cycle_index} | alpha={alpha:0.2f}")
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close(fig)
```


### `try_load_seed_models`

File: [GANtastic-PSF2.0.py](../GANtastic-PSF2.0.py), righe 280–309.

```python
def try_load_seed_models(input_shape, psf_shape):
    """
    Carica generator/discriminator da ./seed/*.h5 se presenti e compatibili.
    Ritorna (generator, discriminator) oppure (None, None).
    Note: this function assumes input_shape/psf_shape already reflect any padding/trimming applied
    to X/Y to match seed expectations.
    """
    if not (os.path.exists(GEN_SEED_PATH) and os.path.exists(DISC_SEED_PATH)):
        return None, None

    try:
        gen = tf.keras.models.load_model(GEN_SEED_PATH, compile=False)
        disc = tf.keras.models.load_model(DISC_SEED_PATH, compile=False)

        gen_in = tuple(gen.input_shape[1:])
        disc_in = tuple(disc.input_shape[1:])

        if tuple(input_shape) != gen_in:
            print(f"[SEED] generator_seed.h5 input mismatch: expected {tuple(input_shape)}, found {gen_in}")
            return None, None
        if tuple(psf_shape) != disc_in:
            print(f"[SEED] discriminator_seed.h5 input mismatch: expected {tuple(psf_shape)}, found {disc_in}")
            return None, None

        print(f"[SEED] Loaded seed models from {SEED_DIR}")
        return gen, disc

    except Exception as e:
        print(f"[SEED] Failed to load seed models: {repr(e)}")
        return None, None
```


### `adjust_X_to_seed_if_needed`

File: [GANtastic-PSF2.0.py](../GANtastic-PSF2.0.py), righe 315–383.

```python
def adjust_X_to_seed_if_needed(X: np.ndarray):
    """
    If generator_seed.h5 exists and expects a telemetry vector of different length than X,
    automatically pad X with zeros (if seed expects longer) or trim trailing columns (if seed expects shorter).
    Also, if saved scaler files (mu/sigma) exist and their shape does not match new X,
    remove them so the scaler will be recomputed.

    Returns (X_new, modified_flag) where modified_flag is True if X was padded or trimmed.
    """
    if not os.path.exists(GEN_SEED_PATH):
        return X, False

    try:
        # load model only to inspect input shape (no compile)
        gen = tf.keras.models.load_model(GEN_SEED_PATH, compile=False)
        gen_input_shape = tuple(gen.input_shape[1:])
        # handle only simple 1-D telemetry input
        if len(gen_input_shape) != 1:
            print("[SEED-ADJUST] Seed generator input is not a 1-D vector; skipping automatic adjustment.")
            return X, False

        desired_len = int(gen_input_shape[0])
        cur_len = X.shape[1]

        if desired_len == cur_len:
            return X, False

        if desired_len > cur_len:
            pad_width = desired_len - cur_len
            print(f"[SEED-ADJUST] Padding X with {pad_width} zeros to match seed input length {desired_len}.")
            pad_array = np.zeros((X.shape[0], pad_width), dtype=X.dtype)
            X_new = np.concatenate([X, pad_array], axis=1)

        else:  # desired_len < cur_len -> trim trailing columns
            trim_width = cur_len - desired_len
            print(f"[SEED-ADJUST] Trimming {trim_width} trailing columns from X to match seed input length {desired_len}.")
            X_new = X[:, :desired_len].copy()

        # If existing scaler files have incompatible shape, remove them so they are recomputed.
        remove_scaler = False
        if os.path.exists(X_MU_PATH) and os.path.exists(X_SIGMA_PATH):
            try:
                mu = np.load(X_MU_PATH)
                sigma = np.load(X_SIGMA_PATH)
                # mu expected shape (1, n_features) or (n_features,)
                if mu.ndim >= 2 and mu.shape[1] != X_new.shape[1]:
                    remove_scaler = True
                elif mu.ndim == 1 and mu.shape[0] != X_new.shape[1]:
                    remove_scaler = True
                if sigma.ndim >= 2 and sigma.shape[1] != X_new.shape[1]:
                    remove_scaler = True
                elif sigma.ndim == 1 and sigma.shape[0] != X_new.shape[1]:
                    remove_scaler = True
            except Exception:
                remove_scaler = True

        if remove_scaler:
            try:
                os.remove(X_MU_PATH)
                os.remove(X_SIGMA_PATH)
                print("[SEED-ADJUST] Removed incompatible scaler files (x_mu/x_sigma) to force recompute.")
            except Exception:
                pass

        return X_new, True

    except Exception as e:
        print(f"[SEED-ADJUST] Error inspecting seed model: {repr(e)}. Skipping adjustment.")
        return X, False
```


### `list_specula_folders`

File: [GANtastic-PSF2.0.py](../GANtastic-PSF2.0.py), righe 389–390.

```python
def list_specula_folders(base_dir: str):
    return sorted(glob.glob(os.path.join(base_dir, "*")))
```


### `crop_center`

File: [GANtastic-PSF2.0.py](../GANtastic-PSF2.0.py), righe 392–396.

```python
def crop_center(frame: np.ndarray, size: int = 64) -> np.ndarray:
    y, x = frame.shape
    startx = x // 2 - size // 2
    starty = y // 2 - size // 2
    return frame[starty:starty + size, startx:startx + size]
```


### `load_data_from_folders`

File: [GANtastic-PSF2.0.py](../GANtastic-PSF2.0.py), righe 398–432.

```python
def load_data_from_folders(folders, start_frame=50, crop_size=64):
    psf_frames = []
    array_commands = []

    for folder in folders:
        psf_path = os.path.join(folder, "psf.fits")
        commands_path = os.path.join(folder, "commands.fits")

        if not (os.path.exists(psf_path) and os.path.exists(commands_path)):
            print(f"[DATA] Missing file in folder: {folder}")
            continue

        with fits.open(psf_path) as hdul:
            psf_cube = hdul[0].data
        if psf_cube.ndim != 3 or psf_cube.shape[0] != 500:
            print(f"[DATA] Unexpected PSF shape {psf_cube.shape} in {folder}")
            continue

        cropped = [crop_center(frame, size=crop_size) for frame in psf_cube]
        psf_frames.extend(cropped[start_frame:])

        with fits.open(commands_path) as hdul:
            commands_array = hdul[0].data
        if commands_array.ndim != 2 or commands_array.shape[0] != 500:
            print(f"[DATA] Unexpected commands shape {commands_array.shape} in {folder}")
            continue

        array_commands.extend(commands_array[start_frame:])

    if len(array_commands) == 0 or len(psf_frames) == 0:
        return None, None

    X = np.array(array_commands, dtype=np.float32)
    Y = np.expand_dims(np.array(psf_frames, dtype=np.float32), axis=-1)
    return X, Y
```


### `fit_or_load_x_scaler`

File: [GANtastic-PSF2.0.py](../GANtastic-PSF2.0.py), righe 438–457.

```python
def fit_or_load_x_scaler(X_train: np.ndarray):
    if os.path.exists(X_MU_PATH) and os.path.exists(X_SIGMA_PATH):
        mu = np.load(X_MU_PATH)
        sigma = np.load(X_SIGMA_PATH)
        # If shapes mismatch, recompute
        if (mu.ndim >= 2 and mu.shape[1] != X_train.shape[1]) or (mu.ndim == 1 and mu.shape[0] != X_train.shape[1]):
            print("[SCALER] Existing scaler has incompatible shape. Recomputing scaler.")
            try:
                os.remove(X_MU_PATH)
                os.remove(X_SIGMA_PATH)
            except Exception:
                pass
        else:
            return mu, sigma

    mu = X_train.mean(axis=0, keepdims=True).astype(np.float32)
    sigma = X_train.std(axis=0, keepdims=True).astype(np.float32) + 1e-12
    np.save(X_MU_PATH, mu)
    np.save(X_SIGMA_PATH, sigma)
    return mu, sigma
```


### `apply_x_scaler`

File: [GANtastic-PSF2.0.py](../GANtastic-PSF2.0.py), righe 459–460.

```python
def apply_x_scaler(X: np.ndarray, mu: np.ndarray, sigma: np.ndarray):
    return (X - mu) / sigma
```


### `normalize_y_per_frame_peak`

File: [GANtastic-PSF2.0.py](../GANtastic-PSF2.0.py), righe 462–464.

```python
def normalize_y_per_frame_peak(Y: np.ndarray):
    peaks = Y.max(axis=(1, 2, 3), keepdims=True) + 1e-12
    return Y / peaks, peaks
```


### `make_datasets_with_norm`

File: [GANtastic-PSF2.0.py](../GANtastic-PSF2.0.py), righe 466–495.

```python
def make_datasets_with_norm(X, Y, batch_size=32):
    X_train, X_val, Y_train, Y_val = train_test_split(X, Y, test_size=0.2, shuffle=False)

    mu, sigma = fit_or_load_x_scaler(X_train)
    X_train = apply_x_scaler(X_train, mu, sigma)
    X_val = apply_x_scaler(X_val, mu, sigma)

    Y_train, _ = normalize_y_per_frame_peak(Y_train)
    Y_val, _ = normalize_y_per_frame_peak(Y_val)

    X_train, Y_train = shuffle(X_train, Y_train, random_state=42)
    X_val, Y_val = shuffle(X_val, Y_val, random_state=42)

    steps_per_epoch = len(X_train) // batch_size
    validation_steps = len(X_val) // batch_size

    train_dataset = (
        tf.data.Dataset.from_tensor_slices((X_train, Y_train))
        .shuffle(1000)
        .batch(batch_size)
        .prefetch(tf.data.AUTOTUNE)
    )

    val_dataset = (
        tf.data.Dataset.from_tensor_slices((X_val, Y_val))
        .batch(batch_size)
        .prefetch(tf.data.AUTOTUNE)
    )

    return train_dataset, val_dataset, steps_per_epoch, validation_steps, (X_val, Y_val)
```


### `save_val_images`

File: [GANtastic-PSF2.0.py](../GANtastic-PSF2.0.py), righe 501–546.

```python
def save_val_images(generator, X_val, Y_val, out_dir, epoch, prefix="val", every=2):
    if (epoch != 0) and ((epoch + 1) % every != 0):
        return
    if X_val is None or Y_val is None or len(X_val) == 0:
        return

    sample_input = X_val[0:1]
    sample_target = Y_val[0:1]

    pred = generator(sample_input, training=False).numpy()[0, :, :, 0]
    tgt = sample_target[0, :, :, 0]

    fits.PrimaryHDU(tgt).writeto(
        os.path.join(out_dir, f"{prefix}_target_epoch_{epoch+1:04d}.fits"),
        overwrite=True,
    )
    fits.PrimaryHDU(pred).writeto(
        os.path.join(out_dir, f"{prefix}_pred_epoch_{epoch+1:04d}.fits"),
        overwrite=True,
    )

    eps = 1e-6
    log_tgt = np.log10(tgt + eps)
    log_pred = np.log10(pred + eps)
    residual = tgt - pred

    fig, axs = plt.subplots(1, 3, figsize=(18, 6))

    im0 = axs[0].imshow(log_tgt, cmap="inferno")
    axs[0].set_title("Target PSF (log10)")
    axs[0].axis("off")
    fig.colorbar(im0, ax=axs[0], fraction=0.046, pad=0.04)

    im1 = axs[1].imshow(log_pred, cmap="inferno")
    axs[1].set_title("Generated PSF (log10)")
    axs[1].axis("off")
    fig.colorbar(im1, ax=axs[1], fraction=0.046, pad=0.04)

    im2 = axs[2].imshow(residual, cmap="RdBu")
    axs[2].set_title("Residual (Target - Gen)")
    axs[2].axis("off")
    fig.colorbar(im2, ax=axs[2], fraction=0.046, pad=0.04)

    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, f"{prefix}_epoch_{epoch+1:04d}.png"), dpi=200)
    plt.close(fig)
```


### `build_generator`

File: [GANtastic-PSF2.0.py](../GANtastic-PSF2.0.py), righe 552–582.

```python
def build_generator(input_shape):
    telemetry_input = Input(shape=input_shape, name="telemetry")

    x = layers.Dense(128, activation="relu")(telemetry_input)
    x = layers.BatchNormalization()(x)
    x = layers.Dropout(0.1)(x)

    x = layers.Dense(50, activation="relu")(x)
    x = layers.Dropout(0.1)(x)

    x = layers.Dense(40, activation="relu")(x)
    x = layers.Dropout(0.1)(x)

    x = layers.Dense(20, activation="relu")(x)
    x = layers.Dropout(0.1)(x)

    x = layers.Dense(256, activation="relu")(x)
    x = layers.Dense(8 * 8 * 1024, activation="relu")(x)
    x = layers.Reshape((8, 8, 1024))(x)

    x = layers.Conv2DTranspose(512, 4, strides=2, padding="same", activation="relu")(x)
    x = layers.BatchNormalization()(x)

    x = layers.Conv2DTranspose(256, 4, strides=2, padding="same", activation="relu")(x)
    x = layers.BatchNormalization()(x)

    x = layers.Conv2DTranspose(128, 4, strides=2, padding="same", activation="relu")(x)
    x = layers.BatchNormalization()(x)

    output = layers.Conv2D(1, 3, padding="same", activation="sigmoid", name="psf")(x)
    return Model(telemetry_input, output, name="generator")
```


### `build_discriminator`

File: [GANtastic-PSF2.0.py](../GANtastic-PSF2.0.py), righe 584–600.

```python
def build_discriminator(psf_shape):
    psf_input = Input(shape=psf_shape, name="psf_in")

    x = layers.Conv2D(64, 4, strides=2, padding="same", activation="relu")(psf_input)
    x = layers.BatchNormalization()(x)

    x = layers.Conv2D(128, 4, strides=2, padding="same", activation="relu")(x)
    x = layers.BatchNormalization()(x)

    x = layers.Conv2D(256, 4, strides=2, padding="same", activation="relu")(x)
    x = layers.BatchNormalization()(x)

    x = layers.Conv2D(256, 4, strides=1, padding="same", activation="relu")(x)
    x = layers.BatchNormalization()(x)

    output = layers.Dense(1)(x)
    return Model(psf_input, output, name="discriminator")
```


### `discriminator_loss`

File: [GANtastic-PSF2.0.py](../GANtastic-PSF2.0.py), righe 608–610.

```python
def discriminator_loss(real_output, fake_output):
    return loss_object(tf.ones_like(real_output), real_output) + \
           loss_object(tf.zeros_like(fake_output), fake_output)
```


### `generator_loss`

File: [GANtastic-PSF2.0.py](../GANtastic-PSF2.0.py), righe 612–620.

```python
def generator_loss(fake_output, generated_image, target_image, lambda_rec, alpha):
    adv_loss = loss_object(tf.ones_like(fake_output), fake_output)
    epsilon = 1e-10

    rec_loss = alpha * tf.reduce_mean(tf.square(target_image - generated_image)) + \
        (1 - alpha) * tf.reduce_mean(
            tf.square(tf.math.log(target_image + epsilon) - tf.math.log(generated_image + epsilon))
        )
    return adv_loss + lambda_rec * rec_loss
```


### `train_step`

File: [GANtastic-PSF2.0.py](../GANtastic-PSF2.0.py), righe 623–645.

```python
def train_step(generator, discriminator, telemetry_batch, real_psf_batch,
               gen_optimizer, disc_optimizer, lambda_rec, alpha):
    with tf.GradientTape() as gen_tape, tf.GradientTape() as disc_tape:
        generated_psf = generator(telemetry_batch, training=True)
        real_output = discriminator(real_psf_batch, training=True)
        fake_output = discriminator(generated_psf, training=True)

        gen_loss = generator_loss(
            fake_output,
            generated_psf,
            real_psf_batch,
            lambda_rec=lambda_rec,
            alpha=alpha
        )
        disc_loss = discriminator_loss(real_output, fake_output)

    gradients_gen = gen_tape.gradient(gen_loss, generator.trainable_variables)
    gradients_disc = disc_tape.gradient(disc_loss, discriminator.trainable_variables)

    gen_optimizer.apply_gradients(zip(gradients_gen, generator.trainable_variables))
    disc_optimizer.apply_gradients(zip(gradients_disc, discriminator.trainable_variables))

    return gen_loss, disc_loss
```


### `_handle_sigint`

File: [GANtastic-PSF2.0.py](../GANtastic-PSF2.0.py), righe 653–654.

```python
def _handle_sigint(sig, frame):
    STOP_REQUESTED["flag"] = True
```


### `main`

File: [GANtastic-PSF2.0.py](../GANtastic-PSF2.0.py), righe 662–961.

```python
def main():
    state = load_state()

    gen_optimizer = tf.keras.optimizers.Adam(2e-4, beta_1=0.5)
    disc_optimizer = tf.keras.optimizers.Adam(2e-4, beta_1=0.5)

    generator = None
    discriminator = None

    # Checkpoint "solido": niente None, solo oggetti trackable
    ckpt = tf.train.Checkpoint(
        gen_optimizer=gen_optimizer,
        disc_optimizer=disc_optimizer,
        global_epoch=tf.Variable(0, dtype=tf.int64),
        best_val_l1=tf.Variable(1e9, dtype=tf.float32),
        wait=tf.Variable(0, dtype=tf.int64),
    )
    ckpt_manager = tf.train.CheckpointManager(ckpt, CKPT_DIR, max_to_keep=5)

    latest_ckpt_path = ckpt_manager.latest_checkpoint
    if latest_ckpt_path:
        print(f"[CKPT] Found checkpoint: {latest_ckpt_path}")
    else:
        print("[CKPT] No checkpoint found. Starting new training.")

    while True:
        if state["global_epoch"] >= MAX_GLOBAL_EPOCHS:
            print(f"[STOP] Reached MAX_GLOBAL_EPOCHS={MAX_GLOBAL_EPOCHS}. Exiting.")
            break

        all_folders = list_specula_folders(BASE_DIR)
        used = set(state["used_folders"])
        new_folders = [f for f in all_folders if f not in used]

        if len(new_folders) == 0:
            print("[DATA] Nessuna nuova simulazione trovata in BASE_DIR.")
            print("[AUTO] Lancio SPECULA per generare nuove simulazioni...")

            # salva stato prima di lanciare
            ckpt_manager.save()
            save_state(state)
            if generator is not None:
                generator.save(LAST_GEN_PATH)

            ok = run_specula_command()
            if not ok:
                print("[AUTO] SPECULA fallito (return != 0). Non posso continuare finché non vengono create nuove simulazioni.")
                print(f"       Controlla il log: {SPECULA_LOG}")
                break

            # dopo SPECULA, ricontrolla
            all_folders = list_specula_folders(BASE_DIR)
            used = set(state["used_folders"])
            new_folders = [f for f in all_folders if f not in used]

            if len(new_folders) == 0:
                print("[AUTO] SPECULA ha finito ma non trovo nuove cartelle in BASE_DIR.")
                print("       Verifica che generate_simulations.py scriva in BASE_DIR e che i nomi cartella siano univoci.")
                break

        print(f"[AUTO] Trovate {len(new_folders)} nuove simulazioni. Continuo.")

        cycle_folders = new_folders[:FOLDERS_PER_CYCLE]

        cycle_idx = int(state.get("cycle_index", 0))
        alpha_cycle = alpha_for_cycle(cycle_idx)
        alpha_tf = tf.constant(alpha_cycle, dtype=tf.float32)

        # Per salvare loss "di questo ciclo"
        cycle_start_global_epoch = int(state["global_epoch"])
        cycle_start_hist_idx = len(state["history"]["gen_loss"])

        print(f"\n=== NEW CYCLE === using {len(cycle_folders)} folders (out of {len(new_folders)} new)")
        print(f"[CYCLE] cycle_index={cycle_idx} -> alpha={alpha_cycle:.2f}")

        X, Y = load_data_from_folders(cycle_folders, start_frame=START_FRAME, crop_size=CROP_SIZE)
        if X is None or Y is None:
            print("[DATA] Caricamento fallito per questo ciclo. Marco cartelle come usate e continuo.")
            state["used_folders"].extend(cycle_folders)
            # anche se salti, incrementa ciclo (hai “consumato” il tentativo di ciclo)
            state["cycle_index"] = cycle_idx + 1
            save_state(state)
            continue

        # --- NEW: pad/trim X if seed expects different input length (e.g., 702 vs 700) ---
        X, modified = adjust_X_to_seed_if_needed(X)
        if modified:
            print(f"[DATA] X adjusted -> new telemetry dimension: {X.shape[1]}")

        # Costruzione modelli: qui sappiamo input_shape/psf_shape
        if generator is None or discriminator is None:
            input_shape = X.shape[1:]
            psf_shape = Y.shape[1:]

            latest_ckpt_path = ckpt_manager.latest_checkpoint

            if latest_ckpt_path:
                # Priorità al checkpoint
                generator = build_generator(input_shape)
                discriminator = build_discriminator(psf_shape)

                ckpt.generator = generator
                ckpt.discriminator = discriminator

                ckpt.restore(latest_ckpt_path).expect_partial()
                print("[CKPT] Restored model + optimizer state.")

                state["global_epoch"] = int(ckpt.global_epoch.numpy())
                state["best_val_l1"] = float(ckpt.best_val_l1.numpy())
                state["wait"] = int(ckpt.wait.numpy())

            else:
                # Nessun checkpoint -> prova seed, altrimenti build da zero
                gen_seed, disc_seed = try_load_seed_models(input_shape, psf_shape)
                if gen_seed is not None and disc_seed is not None:
                    generator = gen_seed
                    discriminator = disc_seed
                    print("[INIT] Using SEED models as starting point.")
                else:
                    generator = build_generator(input_shape)
                    discriminator = build_discriminator(psf_shape)
                    print("[INIT] No checkpoint/seed usable -> starting from scratch.")

                ckpt.generator = generator
                ckpt.discriminator = discriminator

        train_dataset, val_dataset, steps_per_epoch, validation_steps, (X_val, Y_val) = \
            make_datasets_with_norm(X, Y, batch_size=BATCH_SIZE)

        if steps_per_epoch <= 0 or validation_steps <= 0:
            print("[DATA] Dataset troppo piccolo per fare almeno 1 step. Marco cartelle come usate e continuo.")
            state["used_folders"].extend(cycle_folders)
            state["cycle_index"] = cycle_idx + 1
            save_state(state)
            continue

        for local_epoch in range(EPOCHS_PER_CYCLE):
            # Uscita vera SOLO per Ctrl+C
            if STOP_REQUESTED["flag"]:
                break

            epoch = state["global_epoch"]
            print(f"\nEpoch {epoch + 1}  (cycle {local_epoch + 1}/{EPOCHS_PER_CYCLE})")

            progbar = tqdm(
                train_dataset.take(steps_per_epoch),
                total=steps_per_epoch,
                desc="Training",
                ncols=100
            )

            # Media per epoca
            sum_gen = 0.0
            sum_disc = 0.0
            n_batches = 0

            for telemetry_batch, psf_batch in progbar:
                gen_loss, disc_loss = train_step(
                    generator, discriminator,
                    telemetry_batch, psf_batch,
                    gen_optimizer, disc_optimizer,
                    lambda_rec=LAMBDA_REC,
                    alpha=alpha_tf,
                )

                g = float(gen_loss.numpy())
                d = float(disc_loss.numpy())
                sum_gen += g
                sum_disc += d
                n_batches += 1

                progbar.set_postfix({
                    "GenLoss": f"{g:.6f}",
                    "DiscLoss": f"{d:.6f}",
                    "alpha": f"{alpha_cycle:.2f}"
                })

                if STOP_REQUESTED["flag"]:
                    break

            epoch_gen_loss = sum_gen / max(n_batches, 1)
            epoch_disc_loss = sum_disc / max(n_batches, 1)

            val_l1_losses = []
            for telemetry_batch_val, psf_batch_val in val_dataset.take(validation_steps):
                generated_val = generator(telemetry_batch_val, training=False)
                val_l1_losses.append(float(tf.reduce_mean(tf.abs(psf_batch_val - generated_val)).numpy()))
            val_l1_mean = float(np.mean(val_l1_losses)) if len(val_l1_losses) else float("inf")

            state["history"]["gen_loss"].append(epoch_gen_loss)
            state["history"]["disc_loss"].append(epoch_disc_loss)
            state["history"]["val_l1"].append(val_l1_mean)
            state["history"]["alpha"].append(alpha_cycle)
            state["history"]["cycle"].append(cycle_idx)

            print(f"[VAL] L1 mean: {val_l1_mean:.6f}")

            save_val_images(
                generator=generator,
                X_val=X_val,
                Y_val=Y_val,
                out_dir=IMG_DIR,
                epoch=epoch,
                prefix="val",
                every=SAVE_IMG_EVERY
            )

            # "best" tracking: salva best ma NON ferma mai
            if val_l1_mean < state["best_val_l1"]:
                state["best_val_l1"] = val_l1_mean
                state["wait"] = 0
                ckpt.best_val_l1.assign(val_l1_mean)
                ckpt.wait.assign(0)

                generator.save(BEST_GEN_PATH)
                print(f"[SAVE] Best generator saved (val_l1={val_l1_mean:.6f})")
            else:
                state["wait"] += 1
                ckpt.wait.assign(state["wait"])
                print(f"[VAL] No improvement for {state['wait']} epochs.")

                if state["wait"] >= PATIENCE:
                    print("[INFO] Patience reached (no improvement). Continuing anyway.")
                    state["wait"] = 0
                    ckpt.wait.assign(0)

            # increment + save
            state["global_epoch"] += 1
            ckpt.global_epoch.assign(state["global_epoch"])
            ckpt_manager.save()
            save_state(state)

            # Append cumulativo txt
            append_loss_log(
                LOSS_LOG_PATH,
                global_epoch=epoch + 1,   # stampo 1-based come log
                cycle_index=cycle_idx,
                alpha=alpha_cycle,
                gen_loss=epoch_gen_loss,
                disc_loss=epoch_disc_loss,
                val_l1=val_l1_mean
            )

            # Pausa (file PAUSE) oppure Ctrl+C
            if should_pause() or STOP_REQUESTED["flag"]:
                pause_from_file = should_pause() and (not STOP_REQUESTED["flag"])

                print("\n[PAUSE] Pause/stop requested.")
                print("[PAUSE] Saving last generator, checkpoint, and state.")
                generator.save(LAST_GEN_PATH)
                ckpt_manager.save()
                save_state(state)

                print("[PAUSE] Launching SPECULA from command line...")
                run_specula_command()

                if os.path.exists(PAUSE_FILE):
                    os.remove(PAUSE_FILE)
                    print("[PAUSE] Removed PAUSE file -> auto-resume enabled.")

                # ESCE SOLO se era Ctrl+C (STOP_REQUESTED)
                if STOP_REQUESTED["flag"]:
                    print("[STOP] Ctrl+C received -> exiting after SPECULA (checkpoint saved).")
                    break

                # Se era PAUSE da file: non break, si continua automaticamente
                if pause_from_file:
                    print("[PAUSE] Auto-resume after SPECULA (no exit).")

        # Fine ciclo: salva plot+txt per il ciclo corrente (anche se interrotto prima)
        cycle_end_hist_idx = len(state["history"]["gen_loss"])
        if cycle_end_hist_idx > cycle_start_hist_idx:
            n = cycle_end_hist_idx - cycle_start_hist_idx
            epochs = list(range(cycle_start_global_epoch + 1, cycle_start_global_epoch + 1 + n))  # 1-based
            gen_losses = state["history"]["gen_loss"][cycle_start_hist_idx:cycle_end_hist_idx]
            disc_losses = state["history"]["disc_loss"][cycle_start_hist_idx:cycle_end_hist_idx]
            val_l1s = state["history"]["val_l1"][cycle_start_hist_idx:cycle_end_hist_idx]

            png_path = os.path.join(LOSS_DIR, f"loss_cycle_{cycle_idx:04d}.png")
            txt_path = os.path.join(LOSS_DIR, f"loss_cycle_{cycle_idx:04d}.txt")

            save_cycle_loss_png(png_path, epochs, gen_losses, disc_losses, val_l1s, cycle_idx, alpha_cycle)
            save_cycle_loss_txt(txt_path, epochs, gen_losses, disc_losses, val_l1s, cycle_idx, alpha_cycle)

            print(f"[LOSS] Saved cycle loss PNG: {png_path}")
            print(f"[LOSS] Saved cycle loss TXT: {txt_path}")
        else:
            print("[LOSS] No completed epochs in this cycle -> skipping cycle loss PNG/TXT.")

        # Marca cartelle usate + incrementa cycle_index
        state["used_folders"].extend(cycle_folders)
        state["cycle_index"] = cycle_idx + 1
        save_state(state)

        if STOP_REQUESTED["flag"]:
            break

        print("[CYCLE] Cycle completed. Looking for more data...")

    print("\nDone.")
```
