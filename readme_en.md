# Image Anti-Seek

[中文](./readme.md) | [English](./readme_en.md)

This is an **anti-detection** and **privacy protection** extension developed for ComfyUI.

![Encryption](./encryption.png)

### Core Philosophy

The core purpose of this extension is to prevent images from being scanned by machines or viewed without authorization. It introduces an **obfuscation** mechanism: when decryption fails or is probed, it creates a fake image with random geometric shapes to confuse monitoring systems.

### Core Principles

1.  **Noise Encryption**: Uses NumPy to generate a layer of "digital noise" based on a specific seed, and "covers" the original image using an XOR operation.
2.  **Hash Verification**: Calculates the hash of the original image during encryption and stores it (`e_info`) to verify data integrity during decryption.
3.  **Security Salt**: Supports a user-defined [Salt](#webui-settings) value to obfuscate the random seed. Even if the algorithm is public, the image cannot be restored without the salt value.
4.  **Forgery Mechanism**: If a hash mismatch, incorrect salt, or incorrect key name is detected during decryption, the extension automatically generates a **fake image** containing random colors and geometric shapes to achieve the [obfuscation](#core-philosophy) effect.