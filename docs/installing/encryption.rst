.. _encryption:

Encryption
==========

This is a optional step, but has to be chosen to either use or skip in order for the installer to know what to do.
If you wish to have `luks2 (argon2) <https://wiki.archlinux.org/index.php/Dm-crypt/Encrypting_an_entire_system#Btrfs_subvolumes_with_swap>`_ encryption, then all you need to do is select a disk password and select `Enable Disk Encryption`.

If you prefer or can't use encryption, simply choose `Don't use disk encryption` and proceed to the _mirrors step.

.. note:: This step will not start to format the drive when you select a disk, the _Encryption step.

.. image:: encryption.png