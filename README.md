# EEG QC Prototype

Минимальный прототип Quality Check для ЭЭГ-записей. Текущая версия сделана без нейронных сетей: это воспроизводимый signal-processing MVP, который демонстрирует расчёт QC-метрик, формирование таблиц, графиков и HTML-отчёта.

## Что реализовано

- генерация трёх демонстрационных EEG-подобных записей: чистая запись, запись с шумным каналом `Fz`, запись с низкоамплитудным/плоским каналом `Pz`;
- расчёт амплитудных метрик по каналам;
- расчёт спектральной мощности по диапазонам Delta, Theta, Alpha, Beta, Gamma;
- расчёт сводных показателей: `mean_amplitude_uv`, `max_amplitude_uv`, `dominant_frequency_hz`, `alpha_beta_ratio`, `theta_alpha_ratio`, `n_bad_channels`, `qc_status`;
- экспорт двух таблиц в CSV;
- генерация двух SVG-графиков с названием, подписями осей и легендой;
- генерация HTML-отчёта `report.html`.

Полный отчёт по критериям практики: `docs/final_report.md`.

## Быстрый запуск

```powershell
python -m pip install -r requirements.txt
python -m qc_eeg demo --output reports/demo_run
```

После запуска появятся файлы:

- `reports/demo_run/qc_results.csv`;
- `reports/demo_run/test_results.csv`;
- `reports/demo_run/band_power.svg`;
- `reports/demo_run/bad_channels.svg`;
- `reports/demo_run/report.html`.

## Проверка

```powershell
python -m unittest discover -s tests
```

## Источники данных

Текущий MVP использует синтетические EEG-подобные данные, чтобы прототип запускался без закрытых лабораторных записей. Это честный демонстрационный режим: он показывает архитектуру расчёта и отчётности, но не заменяет валидацию на реальных BrainVision-файлах.

## Связь с дальнейшей версией

Файлы исходного прототипа из практики используют MNE, FASTER и HTML-шаблон отчёта. Для сдаваемого MVP логика упрощена так, чтобы основные функции запускались в любом окружении с NumPy. В следующей версии можно вернуть полноценный MNE-пайплайн: чтение `.vhdr/.eeg/.vmrk`, монтаж `.elc`, `mne.Report`, `mne-faster` и пакетную обработку реальных записей.

## GitHub

Репозиторий проекта: https://github.com/LevinAE/QC_EEG_PJCT
