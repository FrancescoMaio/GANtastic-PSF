# 8. Riferimento completo del template YAML

## Catena di elaborazione

L'atmosfera riceve seeing e vento, produce strati per la propagazione. La propagazione combina atmosfera, pupilstop e layer DM ritardato (`dm.out_layer:-1`). Il campo della NGS alimenta il sensore SH e la PSF. Il detector campiona l'intensità SH; lo slope computer produce slopes; il ricostruttore produce modi; l'integratore produce comandi per il DM. Il DataStore salva i modi del ricostruttore con etichetta commands e la PSF con etichetta psf.

Le stringhe con riferimenti, `*_ref`, `*_object`, tag e `class` sono interpretate da SPECULA; questo repository non contiene le implementazioni di tali classi. Il significato preciso di opzioni non spiegate dai commenti deve essere verificato nella versione SPECULA effettivamente usata. La tabella è un inventario esatto dei valori, non una certificazione della compatibilità con una release esterna.

## Parametri da leggere insieme

- `pixel_pupil=360` e `pixel_pitch=0.02255 m` definiscono un'estensione nominale della griglia di 8.118 m; la pupilla effettiva dipende dal tag pupilstop.
- `total_time=0.5 s`, `time_step=0.001 s`, `detector.dt=0.001 s`: il loader assume 500 campioni salvati.
- `source_on_axis` è a [0,0], `source_ngs` a [5,0] arcsec/gradi; entrambe a 768 nm nel template. Le magnitudini 10 vengono sovrascritte dalla griglia.
- Il PSF usa 2200 nm e 13 mas/pixel; la sorgente collegata è NGS, non on-axis.
- `sh.subap_on_diameter=40`, `subap_npx=6`, detector 240×240: controllare coerenza con maschera e subapdata.
- `integrator.delay=2`, `int_gain=[0.30]`, `n_modes=[702]`, `dm.nmodes=702`: controllare insieme ricostruttore e base modale.
- Il template ha 35 strati. Il generatore sostituisce il profilo vento, ma non heights o Cn2.
- `out_sr` è dichiarato tra gli output PSF ma non incluso nell'input_list del DataStore: il template non lo richiede in salvataggio.

## Inventario di tutte le foglie

Le liste sono rappresentate come valori Python equivalenti al YAML; `inf` corrisponde a `.inf` e False/True ai booleani. Consultare il file originale per commenti, unità e stile.

| Percorso | Valore nel template originale |
|---|---|
| `main.class` | `SimulParams` |
| `main.root_dir` | `/home/francesco.maio/SPECULA/ERIS/VLT` |
| `main.pixel_pupil` | `360` |
| `main.pixel_pitch` | `0.02255` |
| `main.total_time` | `0.5` |
| `main.time_step` | `0.001` |
| `main.zenithAngleInDeg` | `30.0` |
| `main.display_server` | `False` |
| `seeing.class` | `WaveGenerator` |
| `seeing.constant` | `0.8` |
| `seeing.outputs` | `['output']` |
| `wind_speed.class` | `WaveGenerator` |
| `wind_speed.constant` | `[5.5, 5.5, 5.1, 5.5, 5.6, 5.7, 5.8, 6.0, 6.5, 7.0, 7.5, 8.5, 9.5, 11.5, 17.5, 23.0, 26.0, 29.0, 32.0, 27.0, 22.0, 14.5, 9.5, 6.3, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0, 10.0]` |
| `wind_speed.outputs` | `['output']` |
| `wind_direction.class` | `WaveGenerator` |
| `wind_direction.constant` | `[0, -180, 0, 0, 90, 180, 0, 0, 0, -180, 0, 0, -90, 0, 90, -180, 90, 0, -90, -90, 0, -90, 0, 0, 180, 180, 0, -180, 90, 0, 0, 180, -90, 90, -90]` |
| `wind_direction.outputs` | `['output']` |
| `source_on_axis.class` | `Source` |
| `source_on_axis.polar_coordinates` | `[0.0, 0.0]` |
| `source_on_axis.magnitude` | `10` |
| `source_on_axis.wavelengthInNm` | `768` |
| `source_ngs.class` | `Source` |
| `source_ngs.polar_coordinates` | `[5.0, 0.0]` |
| `source_ngs.height` | `inf` |
| `source_ngs.magnitude` | `10` |
| `source_ngs.wavelengthInNm` | `768` |
| `pupilstop.class` | `Pupilstop` |
| `pupilstop.tag` | `pupilstop_vlt_360p` |
| `atmo.class` | `AtmoEvolution` |
| `atmo.simul_params_ref` | `main` |
| `atmo.L0` | `25` |
| `atmo.heights` | `[30.0, 90.0, 150.0, 200.0, 245.0, 300.0, 390.0, 600.0, 1130.0, 1880.0, 2630.0, 3500.0, 4500.0, 5500.0, 6500.0, 7500.0, 8500.0, 9500.0, 10500.0, 11500.0, 12500.0, 13500.0, 14500.0, 15500.0, 16500.0, 17500.0, 18500.0, 19500.0, 20500.0, 21500.0, 22500.0, 23500.0, 24500.0, 25500.0, 26500.0]` |
| `atmo.Cn2` | `[0.241954, 0.119977, 0.0968817, 0.0589889, 0.0472911, 0.0472911, 0.0472911, 0.0472911, 0.0398925, 0.0323939, 0.0161969, 0.0260951, 0.0155971, 0.010398, 0.00999811, 0.0119977, 0.00400924, 0.0139974, 0.0129975, 0.00700868, 0.015997, 0.0258951, 0.0190964, 0.00986813, 0.00616883, 0.00400924, 0.00246953, 0.00215959, 0.00184965, 0.00135974, 0.00110979, 0.000616883, 0.000925825, 0.000493907, 0.000431918]` |
| `atmo.fov` | `120.0` |
| `atmo.inputs.seeing` | `seeing.output` |
| `atmo.inputs.wind_speed` | `wind_speed.output` |
| `atmo.inputs.wind_direction` | `wind_direction.output` |
| `atmo.outputs` | `['layer_list']` |
| `prop.class` | `AtmoPropagation` |
| `prop.simul_params_ref` | `main` |
| `prop.source_dict_ref` | `['source_on_axis', 'source_ngs']` |
| `prop.inputs.atmo_layer_list` | `['atmo.layer_list']` |
| `prop.inputs.common_layer_list` | `['pupilstop', 'dm.out_layer:-1']` |
| `prop.outputs` | `['out_source_on_axis_ef', 'out_source_ngs_ef']` |
| `sh.class` | `SH` |
| `sh.subap_on_diameter` | `40` |
| `sh.subap_wanted_fov` | `2.4` |
| `sh.sensor_pxscale` | `0.4` |
| `sh.subap_npx` | `6` |
| `sh.wavelengthInNm` | `768` |
| `sh.inputs.in_ef` | `prop.out_source_ngs_ef` |
| `sh.outputs` | `['out_i']` |
| `detector.class` | `CCD` |
| `detector.simul_params_ref` | `main` |
| `detector.size` | `[240, 240]` |
| `detector.dt` | `0.001` |
| `detector.bandw` | `400` |
| `detector.photon_noise` | `True` |
| `detector.readout_noise` | `True` |
| `detector.excess_noise` | `True` |
| `detector.readout_level` | `0.2` |
| `detector.quantum_eff` | `0.3` |
| `detector.inputs.in_i` | `sh.out_i` |
| `detector.outputs` | `['out_pixels']` |
| `slopec.class` | `ShSlopec` |
| `slopec.thr_value` | `0` |
| `slopec.subapdata_object` | `subapdata_vlt` |
| `slopec.weightedPixRad` | `2` |
| `slopec.interleave` | `True` |
| `slopec.inputs.in_pixels` | `detector.out_pixels` |
| `slopec.outputs` | `['out_slopes']` |
| `modalrec.class` | `Modalrec` |
| `modalrec.recmat_object` | `eris_rec_test` |
| `modalrec.inputs.in_slopes` | `slopec.out_slopes` |
| `modalrec.outputs` | `['out_modes']` |
| `integrator.class` | `Integrator` |
| `integrator.simul_params_ref` | `main` |
| `integrator.delay` | `2` |
| `integrator.int_gain` | `[0.3]` |
| `integrator.n_modes` | `[702]` |
| `integrator.inputs.delta_comm` | `modalrec.out_modes` |
| `integrator.outputs` | `['out_comm']` |
| `dm.class` | `DM` |
| `dm.simul_params_ref` | `main` |
| `dm.ifunc_object` | `DSMifuncZonal360pV1` |
| `dm.m2c_object` | `modal_base_vlt` |
| `dm.nmodes` | `702` |
| `dm.height` | `0` |
| `dm.inputs.in_command` | `integrator.out_comm` |
| `dm.outputs` | `['out_layer']` |
| `psf.class` | `PSF` |
| `psf.simul_params_ref` | `main` |
| `psf.wavelengthInNm` | `2200` |
| `psf.pixel_size_mas` | `13` |
| `psf.start_time` | `0.05` |
| `psf.inputs.in_ef` | `prop.out_source_ngs_ef` |
| `psf.outputs` | `['out_psf', 'out_sr']` |
| `data_store.class` | `DataStore` |
| `data_store.store_dir` | `./data/sims` |
| `data_store.inputs.input_list` | `['commands-modalrec.out_modes', 'psf-psf.out_psf']` |

Somma numerica dei 35 pesi Cn2 inclusi: `0.999999663000`. Il valore è coerente con somma unitaria entro l’arrotondamento; non è stata applicata alcuna rinormalizzazione in questa consegna.
