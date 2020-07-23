Arch Linux GUI Installer
========================

| Archinstall GUI is a graphical installer.
| The goal is to make it easier for new users to try Arch Linux before fully committing to understand all mechanics.
| `Torxed <https://github.com/Torxed>`_ still recommends reading the Official `Installation guide <https://wiki.archlinux.org/index.php/installation_guide>`_ to learn and understand how Arch Linux actually works.

Some of the features of ArchInstall GUI are:

* **Minimal setup.** by default installs as few packages as possible while still allowing for a good user experience.

* **Easy disk encryption.** The installer makes it easy to set up good disk encryption.

* **AUR support.** There's an option to enable *(and install)* AUR packages and package manager.

.. warning:: As of v0.1 there's no option to partition the selected disk. There for, the entire disk will be used. If you're looking to partition a disk in another way, the official `Installation guide <https://wiki.archlinux.org/index.php/installation_guide>`_ is the way to go.

.. image:: installer_overview.png

.. toctree::
   :maxdepth: 3
   :caption: Installation

   installing/harddrive.rst
   installing/encryption.rst
   installing/mirrors.rst
   installing/arch_linux.rst
   installing/language.rst
   installing/profiles.rst
   installing/applications.rst
   installing/accounts.rst
   installing/aur_packages.rst

.. toctree::
   :maxdepth: 3
   :caption: Getting help

   help/discord
   help/issues

.. toctree::
   :maxdepth: 3
   :caption: Creating a ISO

   ISO/index.rst

.. toctree::
   :maxdepth: 3
   :caption: Profiles

   profiles/index.rst