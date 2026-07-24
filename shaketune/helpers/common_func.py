# Shake&Tune: 3D printer analysis tools
#
#
# Licensed under the GNU General Public License v3.0 (GPL-3.0)
#
# File: common_func.py
# Description: Contains common functions and constants used across the Shake&Tune
#              package for 3D printer vibration analysis and diagnostics.


import math
from pathlib import Path

import numpy as np

# Constant used to define the standard axis direction and names
AXIS_CONFIG = [
    {'axis': 'x', 'direction': (1, 0, 0), 'label': 'axis_X'},
    {'axis': 'y', 'direction': (0, 1, 0), 'label': 'axis_Y'},
    {'axis': 'a', 'direction': (1, -1, 0), 'label': 'belt_A'},
    {'axis': 'b', 'direction': (1, 1, 0), 'label': 'belt_B'},
    {'axis': 'corexz_x', 'direction': (1, 0, 1), 'label': 'belt_X'},
    {'axis': 'corexz_z', 'direction': (-1, 0, 1), 'label': 'belt_Z'},
]


# This is used to print the current S&T version on top of the png graph file
def get_git_version():
    try:
        # Get the absolute path of the script, resolving any symlinks
        # Then get 2 times to parent dir to be at the git root folder
        from git import GitCommandError, Repo

        script_path = Path(__file__).resolve()
        repo_path = script_path.parents[1]
        repo = Repo(repo_path)

        try:
            version = repo.git.describe('--tags')
        except GitCommandError:
            # If no tag is found, use the simplified commit SHA instead
            version = repo.head.commit.hexsha[:7]
        return version

    except (ImportError, AttributeError):
        return None

# Compute natural resonant frequency and damping ratio by using the half power bandwidth method with interpolated frequencies
def compute_mechanical_parameters(psd, freqs, min_freq=None):
    max_under_min_freq = False

    if min_freq is not None:
        min_freq_index = np.searchsorted(freqs, min_freq, side='left')
        if min_freq_index >= len(freqs):
            return None, None, None, max_under_min_freq
        if np.argmax(psd) < min_freq_index:
            max_under_min_freq = True
    else:
        min_freq_index = 0

    # Consider only the part of the signal above min_freq
    psd_above_min_freq = psd[min_freq_index:]
    if len(psd_above_min_freq) == 0:
        return None, None, None, max_under_min_freq

    max_power_index_above_min_freq = np.argmax(psd_above_min_freq)
    max_power_index = max_power_index_above_min_freq + min_freq_index
    fr = freqs[max_power_index]
    max_power = psd[max_power_index]

    half_power = max_power / math.sqrt(2)
    indices_below = np.where(psd[:max_power_index] <= half_power)[0]
    indices_above = np.where(psd[max_power_index:] <= half_power)[0]

    # If we are not able to find points around the half power, we can't compute the damping ratio and return None instead
    if len(indices_below) == 0 or len(indices_above) == 0:
        return fr, None, max_power_index, max_under_min_freq

    idx_below = indices_below[-1]
    idx_above = indices_above[0] + max_power_index
    freq_below_half_power = freqs[idx_below] + (half_power - psd[idx_below]) * (
        freqs[idx_below + 1] - freqs[idx_below]
    ) / (psd[idx_below + 1] - psd[idx_below])
    freq_above_half_power = freqs[idx_above - 1] + (half_power - psd[idx_above - 1]) * (
        freqs[idx_above] - freqs[idx_above - 1]
    ) / (psd[idx_above] - psd[idx_above - 1])

    bandwidth = freq_above_half_power - freq_below_half_power
    bw1 = math.pow(bandwidth / fr, 2)
    bw2 = math.pow(bandwidth / fr, 4)

    try:
        zeta = math.sqrt(0.5 - math.sqrt(1 / (4 + 4 * bw1 - bw2)))
    except ValueError:
        # If a math problem arise such as a negative sqrt term, we also return None instead for damping ratio
        return fr, None, max_power_index, max_under_min_freq

    return fr, zeta, max_power_index, max_under_min_freq


# This find all the peaks in a curve by looking at when the derivative term goes from positive to negative
# Then only the peaks found above a threshold are kept to avoid capturing peaks in the low amplitude noise of a signal
def detect_peaks(data: np.ndarray, indices, detection_threshold, relative_height_threshold=None, window_size=5, vicinity=3):
    # Smooth the curve using a moving average to avoid catching peaks everywhere in noisy signals
    # Ensure data is a 1D float array for numpy.convolve
    data_for_convolve = np.asarray(data, dtype=np.float64)
    kernel = np.ones(window_size, dtype=np.float64) / window_size
    smoothed_data = np.convolve(data_for_convolve, kernel, mode='valid')  # type: ignore[arg-type]
    pad_left = window_size // 2
    pad_right = window_size - 1 - pad_left
    smoothed_data = np.concatenate(([smoothed_data[0]] * pad_left, smoothed_data, [smoothed_data[-1]] * pad_right))

    # Find peaks on the smoothed curve
    smoothed_peaks = (
        np.where((smoothed_data[:-2] < smoothed_data[1:-1]) & (smoothed_data[1:-1] > smoothed_data[2:]))[0] + 1
    )
    smoothed_peaks = smoothed_peaks[smoothed_data[smoothed_peaks] > detection_threshold]

    # Additional validation for peaks based on relative height
    valid_peaks = smoothed_peaks
    if relative_height_threshold is not None:
        valid_peaks = []
        for peak in smoothed_peaks:
            peak_height = smoothed_data[peak] - np.min(
                smoothed_data[max(0, peak - vicinity) : min(len(smoothed_data), peak + vicinity + 1)]
            )
            if peak_height > relative_height_threshold * smoothed_data[peak]:
                valid_peaks.append(peak)

    # Refine peak positions on the original curve
    refined_peaks = []
    for peak in valid_peaks:
        local_max = peak + np.argmax(data[max(0, peak - vicinity) : min(len(data), peak + vicinity + 1)]) - vicinity
        refined_peaks.append(local_max)

    num_peaks = len(refined_peaks)

    return num_peaks, np.array(refined_peaks), indices[refined_peaks]


# The goal is to find zone outside of peaks (flat low energy zones) in a signal
def identify_low_energy_zones(power_total, detection_threshold=0.1):
    valleys = []

    # Calculate the mean energy as "mean + 1/4" and standard deviation of the entire power_total
    mean_energy = np.mean(power_total) + (np.max(power_total) - np.min(power_total)) / 4
    std_energy = np.std(power_total)

    # Define a threshold value as "mean + 1/4" minus a certain number of standard deviations
    threshold_value = mean_energy - detection_threshold * std_energy

    # Find valleys in power_total based on the threshold
    in_valley = False
    start_idx = 0
    for i, value in enumerate(power_total):
        if not in_valley and value < threshold_value:
            in_valley = True
            start_idx = i
        elif in_valley and value >= threshold_value:
            in_valley = False
            valleys.append((start_idx, i))

    # If the last point is still in a valley, close the valley
    if in_valley:
        valleys.append((start_idx, len(power_total) - 1))

    max_signal = np.max(power_total)

    # Calculate mean energy for each valley as a percentage of the maximum of the signal
    valley_means_percentage = []
    for start, end in valleys:
        if not np.isnan(np.mean(power_total[start:end])):
            valley_means_percentage.append((start, end, (np.mean(power_total[start:end]) / max_signal) * 100))

    # Sort valleys based on mean percentage values
    sorted_valleys = sorted(valley_means_percentage, key=lambda x: x[2])

    return sorted_valleys
