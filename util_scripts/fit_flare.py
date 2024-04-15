import argparse
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from astropy.io import fits
from astropy.table import Table

###############################################################################


def gaussrise_expdecay(t, t0, f0, A, tau_rise, tau_decay):
    """
    Gaussian rise, exponential decay flare model.

    Parameters
    ----------
    t : float
        Time.
    t0 : float
        Time of flare peak.
    f0 : float
        Baseline flux.
    A : float
        Amplitude of flare.
    tau_rise : float
        Rise time constant.
    tau_decay : float
        Decay time constant.

    Returns
    -------
    float
        Flux at time t.
    """
    return f0 + A * (
        np.where(t < t0, 1, 0) * np.exp(-0.5 * ((t - t0) / tau_rise) ** 2)
        + np.where(t < t0, 0, 1) * np.exp((t - t0) / tau_decay)
    )


def fit_flare(t, f, model, p0=None):
    """
    Fit a flare model to a light curve.

    Parameters
    ----------
    t : array-like
        Time.
    f : array-like
        Flux.
    model : function
        Flare model.
    p0 : array-like, optional
        Initial guess for model parameters.

    Returns
    -------
    array-like
        Best-fit model parameters.
    """

    # Fit model
    popt, pcov = curve_fit(model, t, f, p0=p0)

    return popt, pcov


###############################################################################

if __name__ == "__main__":
    ##############################
    ###     Setup argparse     ###
    ##############################

    # parser object
    parser = argparse.ArgumentParser("Fit a flare model to a light curve.")

    # Photometry file
    parser.add_argument(
        "file_phot", type=str, help="Path to file containing photometry."
    )

    # Model
    parser.add_argument(
        "-m",
        "--model",
        type=str,
        help="Model to fit to the light curve.",
        default="gaussrise_expdecay",
    )

    ##############################
    ###          Setup         ###
    ##############################

    # Parse args
    args = parser.parse_args()

    # Read in photometry
    data_phot = Table(fits.open(args.file_phot)[1].data)

    # Drop nans
    data_phot = data_phot[
        ~np.isnan(data_phot["MAG_FPHOT"]) & ~np.isnan(data_phot["MJD_OBS"])
    ]

    # Choose model, initial params
    if args.model == "gaussrise_expdecay":
        model = gaussrise_expdecay

    # Fit model filter by filter
    popts = {}
    for filt in np.unique(data_phot["FILTER"]):
        # Select filter data
        data_phot_filt = data_phot[data_phot["FILTER"] == filt]

        # Calculate flux
        data_phot_filt["FLUX"] = 10 ** (
            -0.4 * (data_phot_filt["MAG_FPHOT"] - data_phot_filt["ZP_FPHOT"][-1])
        )

        # Select initial guess
        t0 = data_phot_filt["MJD_OBS"][np.argmax(data_phot_filt["FLUX"])]
        f0 = np.median(data_phot_filt["FLUX"])
        A = np.max(data_phot_filt["FLUX"]) - f0
        tau_rise = 10
        tau_decay = 10
        p0 = [t0, f0, A, tau_rise, tau_decay]

        # Fit model
        popts[filt] = fit_flare(
            data_phot_filt["MJD_OBS"], data_phot_filt["FLUX"], model, p0=p0
        )[0]

    # Plot light curve and best-fit model
    tsamp = np.linspace(np.min(data_phot["MJD_OBS"]), np.max(data_phot["MJD_OBS"]), 100)
    for filt, popt in popts.items():
        # Select filter data
        data_phot_filt = data_phot[data_phot["FILTER"] == filt]

        # Calculate flux
        data_phot_filt["FLUX"] = 10 ** (
            -0.4 * (data_phot_filt["MAG_FPHOT"] - data_phot_filt["ZP_FPHOT"][-1])
        )

        plt.plot(
            data_phot_filt["MJD_OBS"],
            data_phot_filt["FLUX"],
            label=f"Data {filt}",
            ls="",
            marker="o",
        )
        plt.plot(
            tsamp,
            gaussrise_expdecay(tsamp, *popt),
            label=f"Model {filt}",
        )
        print(
            f"{filt}: t0={popt[0]:.2f}, f0={popt[1]:.2f}, A={popt[2]:.2f}, tau_rise={popt[3]:.2f}, tau_decay={popt[4]:.2f}"
        )
    plt.xlabel("Time")
    plt.ylabel("Flux")
    plt.legend()
    plt.show()
