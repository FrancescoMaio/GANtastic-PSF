#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
generate_simulations.py

Cosa fa:
1) Genera N file YAML (config) a partire da template.yml con parametri randomizzati.
2) Lancia SPECULA per ciascun YAML:
       specula <config.yml>
3) Salva stdout/stderr di ogni run in un log dedicato.

Struttura output:
./data/
  configs/<run_id>/config_*.yml
  logs/<run_id>/config_*.log
  sims/<run_id>/              (directory “standard”; SPECULA scriverà qui solo se il template lo usa)

NOTE:
- L'output PSF/slopes ecc. è scritto da SPECULA dove previsto dal YAML o dalle sue regole.
- 'specula' deve essere nel PATH.

Uso:
  python generate_simulations.py
  python generate_simulations.py --n 20 --seed 42
  python generate_simulations.py --run-id myrun
  python generate_simulations.py --dry-run
"""

from __future__ import annotations

import argparse
import itertools
import os
import random
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

import numpy as np
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq


# ----------------------------
# Parametri simulazioni
# ----------------------------

@dataclass(frozen=True)
class ParamGrid:
    zenith_angles: List[int]
    seeings: List[float]
    mags: List[int]          # unica magnitudine: on-axis == NGS
    L0s: List[int]
    nmodes_list: List[int]


DEFAULT_GRID = ParamGrid(
    zenith_angles=[40, 50, 70, 80],
    seeings=[0.2, 0.4, 0.8, 1.0],
    mags=[4, 5, 6, 7, 8],    # on-axis == NGS
    L0s=[25, 30],
    nmodes_list=[702],
)


# ----------------------------
# YAML round-trip
# ----------------------------

def _yaml_rt() -> YAML:
    y = YAML()
    y.preserve_quotes = True
    y.indent(mapping=2, sequence=4, offset=2)
    return y


def load_template(template_path: Path) -> CommentedMap:
    y = _yaml_rt()
    with template_path.open("r", encoding="utf-8") as f:
        template = y.load(f)
    if template is None:
        raise RuntimeError(f"Template vuoto o non valido: {template_path}")
    return template


def dump_yaml(config: CommentedMap, out_path: Path) -> None:
    y = _yaml_rt()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        y.dump(config, f)


# ----------------------------
# Wind generation
# ----------------------------

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


def make_wind_dirs(rng_py: random.Random) -> CommentedSeq:
    dirs = [rng_py.choice([0, 90, -90, 180, -180]) for _ in range(35)]
    seq = CommentedSeq(dirs)
    seq.fa.set_flow_style()
    return seq


# ----------------------------
# Config generation
# ----------------------------

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


# ----------------------------
# Run SPECULA
# ----------------------------

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


# ----------------------------
# Cleanup logic (tutti gli output)
# ----------------------------

def dir_has_anything(path: Path) -> bool:
    """True se la directory esiste e contiene almeno un file/cartella."""
    if not path.exists() or not path.is_dir():
        return False
    try:
        next(path.iterdir())
        return True
    except StopIteration:
        return False


def wipe_run_outputs(*paths: Path) -> None:
    """Cancella completamente le directory passate e le ricrea vuote."""
    for p in paths:
        if p.exists():
            shutil.rmtree(p)
        p.mkdir(parents=True, exist_ok=True)


# ----------------------------
# Main
# ----------------------------

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


if __name__ == "__main__":
    raise SystemExit(main())
