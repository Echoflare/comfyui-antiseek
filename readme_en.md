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

### Encryption Feature Configuration

#### Configuration File

Edit the config.json file to configure:

```json
{
    "antiseek_salt": "",
    "antiseek_keyname": "s_tag"
}
```

#### Configuration Parameter Description

1.  **Anti-seek Salt (antiseek_salt)**: Set a custom string. Only clients/CLIs with the same salt value can restore the image. Defaults to empty.
2.  **Metadata Key Name (antiseek_keyname)**: Customize the key name for storing the seed (defaults to `s_tag`) to prevent easy scanning and location.

### Command Line Tool

If you need to decrypt/encrypt images, you can visit [this page](https://github.com/Echoflare/sd-webui-antiseek/blob/main/tools/cli.py) to download the relevant script. This command-line tool can restore encrypted images to their original state and also encrypt regular images. It fully supports user-defined salt and key name parameters. [Online Version](https://echoflare.github.io/antiseek-web/)

For instructions on using the command-line tool, please refer to [this page](https://github.com/Echoflare/sd-webui-antiseek/blob/main/readme_en.md#command-line-tool-toolsclipy).