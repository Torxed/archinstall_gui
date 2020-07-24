Arch Linux GUI Installer
========================

| ArchInstall GUI is a graphical installer for Arch Linux. Where the goal is to make it easier for *new users* to try Arch Linux - before fully committing and understand all the mechanics.

.. warning:: Do not report issues to the Arch Linux forums, this is not an official app. Please ask questions in Arch Install GUI :ref:`discord` server or the :ref:`issues`.

.. note:: You're highly encouraged to read the Official `Installation guide <https://wiki.archlinux.org/index.php/installation_guide>`_ to learn and understand how Arch Linux actually works, automation tools can make users unaware of how something actual works, so read up!

Some of the features of ArchInstall GUI are:

* **Minimal setup.** by default archinstall will install as few packages as possible while still allowing for and maintain a good user experience.

* **Easy disk encryption.** The installer makes it easy to set up good disk encryption.

* **AUR support.** There's an option to enable *(and install)* AUR packages. This support is provided by `yay <https://github.com/Jguer/yay>`_.

.. warning:: As of v0.1 there's no option to partition the selected disk. There for, the entire disk will be used. If you're looking to partition a disk in another way, the official `Installation guide <https://wiki.archlinux.org/index.php/installation_guide>`_ is the way to go.

Below is a screenshot of how the installer looks. Further down in the documentation, all the steps are also described in more detail. A video guide can be found on |youtube|

.. image:: installer_overview.png

.. |youtube| raw:: html

   <a target="_blank" href="https://youtu.be/ZRRSUxGF_Es"><img src="_static/youtube_logo.png" width="60px" alt="Youtube link"></a>

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