# Deploy Steps

## 01 Enable SEV on the Host

1. Manually check whether SEV is among the CPU flags:

``` shell
grep -w sev /proc/cpuinfo
```

2. Follow the similar steps mentioned [here](https://lenovopress.lenovo.com/lp1894.pdf) to enable the AMD security features SME, SEV, and SEV-ES in BIOS/UEFI.
3. Enable SEV in the kernel, append these parameters to `/etc/default/grub`:

``` shell
mem_encrypt=on kvm_amd.sev=1
```

3. After rebooting the host, you should see SEV being enabled in the kernel:

```
$ cat /sys/module/kvm_amd/parameters/sev
Y
```

4. Check SEV support in the virt stack
   Reference: https://libvirt.org/kbase/launch_security_sev.html

## 02 Use virt-manager ([Virtual Machine Manager](https://virt-manager.org/)) to manage CVMs

1. Create a VM with virt-manager with OVMF as its UEFI firmware.
2. Duplicate a xml configuration file as the template for creating a CVM.

- Modify the `name` and `uid`.
- Modify the nvram file `nvram`, disk `source` and MAC address `mac address`.
- Append a `launchSecurity` property to the xml file of the CVM.

``` xml
<memoryBacking>
    <locked/>
</memoryBacking>

<launchSecurity type='sev'>
    <cbitpos>47</cbitpos>
    <reducedPhysBits>1</reducedPhysBits>
    <policy>0x0005</policy>
</launchSecurity>
```

3. Boot the CVM as the Host to deploy the model and the monitor.

## 03 Deploy the models

1. Create a project with a virtual environment (Commands might slightly differ on Windows).

```bash
$ cd model-deploy
$ python3 -m venv venv
```

2. Activate it

```bash
$ . venv/bin/activate
```

or on Windows

```bash
venv\\Scripts\\activate
```

3. Install Flask and PyTorch

```bash
$ pip install Flask
$ pip install torch torchvision
```

4. Install gunicorn

```bash
pip install gunicorn
```

5. Run the models

```bash
gunicorn -b 127.0.0.1:5000 local_keras:app
```

## 04 Prepare the test files

1. Replace the files in `SFAIR/assessor/input`, but must have the subfolder named `men` and `women`. For fairness, use `blackmen`, `blackwomen`, `whitemen`, `whitewomen`.

2. Then run `ground_truth.py` to get the ground truth file; the results are saved in `ground_truth.json`.

## 05 Run the model

1. Run `register.py` to register the remote model. The results are saved in `model.json`.

```bash
python register.py <path_to_the_model>
```

2. Run `monitor.py` in `SFAIR/monitor`. This should not output anything before running `assessor.py`.

```bash
python monitor.py
```

## 06 Run the assessor

1. Boot another CVM to run the assessor that assesses the property of the model.

2. Run `assessor.py` to get the assessment results.

```bash
python assessor.py
```















