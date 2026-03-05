# 🖥️ Rekomendasi Hardware untuk PDAM Chatbot AI

## Performance Target: Response Time < 10 Detik

Dokumen ini berisi rekomendasi hardware lengkap untuk mencapai performa optimal chatbot AI dengan response time di bawah 10 detik.

---

## 📊 Perbandingan Tier Hardware

| Tier | Response Time | Budget (IDR) | Use Case |
|------|---------------|--------------|----------|
| **Entry** | 15-30 detik | 15-25 Juta | Testing, Development |
| **Standard** | 8-15 detik | 35-50 Juta | Production kecil-menengah |
| **Professional** | 3-8 detik | 70-100 Juta | Production enterprise |
| **Ultimate** | 1-3 detik | 150-250 Juta | High-traffic, Real-time |

---

## 🏆 REKOMENDASI TIER 1: PROFESSIONAL (Recommended)

**Target: Response Time 3-8 detik | Budget: ~80-100 Juta**

### Processor (CPU)
| Komponen | Spesifikasi | Harga (IDR) |
|----------|-------------|-------------|
| **Intel Core i9-14900K** | 24 Core (8P+16E), 32 Thread, 6.0GHz | ~10.500.000 |
| **Alternatif: AMD Ryzen 9 7950X** | 16 Core, 32 Thread, 5.7GHz | ~9.800.000 |

**Kenapa penting?**
- Ollama menggunakan CPU untuk tokenization dan preprocessing
- Lebih banyak core = lebih banyak parallel requests
- High clock speed = faster single-thread operations

### GPU (CRITICAL!)
| Komponen | Spesifikasi | Harga (IDR) |
|----------|-------------|-------------|
| **NVIDIA RTX 4090** | 24GB VRAM, 16384 CUDA Cores | ~32.000.000 |
| **Alternatif: NVIDIA RTX 4080 SUPER** | 16GB VRAM, 10240 CUDA Cores | ~19.000.000 |
| **Budget: NVIDIA RTX 4070 Ti SUPER** | 16GB VRAM, 8448 CUDA Cores | ~14.000.000 |

**Kenapa GPU paling penting?**
- LLM inference 10-50x lebih cepat dengan GPU
- VRAM menentukan ukuran model yang bisa di-load
- CUDA cores = parallel processing power

**Tabel Model vs VRAM:**
| Model | Parameter | VRAM Minimum | VRAM Recommended |
|-------|-----------|--------------|------------------|
| Llama 3.2 1B | 1B | 2GB | 4GB |
| Llama 3.2 3B | 3B | 4GB | 8GB |
| Mistral 7B | 7B | 8GB | 12GB |
| Llama 3.1 8B | 8B | 10GB | 16GB |
| Llama 3.1 70B | 70B | 48GB | 80GB |

### RAM (Memory)
| Komponen | Spesifikasi | Harga (IDR) |
|----------|-------------|-------------|
| **G.Skill Trident Z5 RGB** | 64GB (2x32GB) DDR5-6400 CL32 | ~4.500.000 |
| **Alternatif: Kingston Fury Beast** | 64GB (2x32GB) DDR5-5600 | ~3.200.000 |

**Kenapa 64GB?**
- OS + Docker overhead: ~8GB
- Redis cache: 2-4GB
- ChromaDB vector storage: 4-8GB
- Python backend: 2-4GB
- Ollama (CPU fallback): ~16GB
- Headroom for spikes: 20GB+

### Storage (NVMe)
| Komponen | Spesifikasi | Harga (IDR) |
|----------|-------------|-------------|
| **Samsung 990 Pro** | 2TB NVMe Gen4, 7450/6900 MB/s | ~3.500.000 |
| **Backup: Samsung 870 EVO** | 2TB SATA SSD | ~2.800.000 |

**Kenapa NVMe penting?**
- Vector database read/write speed
- Model loading time
- Document processing

### Motherboard
| Komponen | Spesifikasi | Harga (IDR) |
|----------|-------------|-------------|
| **ASUS ROG MAXIMUS Z790 HERO** | Intel Z790, DDR5, PCIe 5.0 | ~9.500.000 |
| **Alternatif: MSI MEG Z790 ACE** | Intel Z790, DDR5, PCIe 5.0 | ~8.500.000 |
| **AMD: ASUS ROG Crosshair X670E Hero** | AMD X670E, DDR5, PCIe 5.0 | ~8.800.000 |

**Fitur penting:**
- PCIe 5.0 x16 slot untuk GPU
- 4+ M.2 NVMe slots
- 2.5Gb atau 10Gb Ethernet
- Good VRM untuk overclocking

### Power Supply (PSU)
| Komponen | Spesifikasi | Harga (IDR) |
|----------|-------------|-------------|
| **Corsair HX1500i** | 1500W 80+ Platinum, Full Modular | ~5.500.000 |
| **Alternatif: Seasonic PRIME TX-1300** | 1300W 80+ Titanium | ~5.200.000 |

**Perhitungan daya:**
- CPU (i9-14900K): ~250W peak
- GPU (RTX 4090): ~450W peak
- Motherboard + RAM: ~100W
- Storage + Fans: ~50W
- **Total: ~850W** (PSU 1200W+ recommended)

### Cooling
| Komponen | Spesifikasi | Harga (IDR) |
|----------|-------------|-------------|
| **NZXT Kraken Z73 RGB** | 360mm AIO, LCD Display | ~4.500.000 |
| **Alternatif: Arctic Liquid Freezer II 360** | 360mm AIO | ~2.200.000 |

### Casing
| Komponen | Spesifikasi | Harga (IDR) |
|----------|-------------|-------------|
| **Lian Li O11 Dynamic EVO** | Full Tower, Good Airflow | ~2.500.000 |
| **Alternatif: Fractal Design Torrent** | High Airflow | ~2.800.000 |

### Network
| Komponen | Spesifikasi | Harga (IDR) |
|----------|-------------|-------------|
| **Intel X550-T2** | 10GbE Dual Port PCIe | ~3.500.000 |
| **Alternatif: Onboard 2.5GbE** | Sudah include di motherboard | - |

---

## 📋 BILL OF MATERIALS - TIER PROFESSIONAL

### Konfigurasi Intel (Recommended)

| No | Komponen | Spesifikasi | Harga (IDR) |
|----|----------|-------------|-------------|
| 1 | CPU | Intel Core i9-14900K | 10.500.000 |
| 2 | GPU | NVIDIA RTX 4090 24GB | 32.000.000 |
| 3 | Motherboard | ASUS ROG MAXIMUS Z790 HERO | 9.500.000 |
| 4 | RAM | G.Skill Trident Z5 64GB DDR5-6400 | 4.500.000 |
| 5 | Storage 1 | Samsung 990 Pro 2TB NVMe | 3.500.000 |
| 6 | Storage 2 | Samsung 870 EVO 2TB SATA | 2.800.000 |
| 7 | PSU | Corsair HX1500i 1500W | 5.500.000 |
| 8 | Cooler | NZXT Kraken Z73 360mm | 4.500.000 |
| 9 | Case | Lian Li O11 Dynamic EVO | 2.500.000 |
| 10 | Fans | Arctic P12 PWM PST (6x) | 600.000 |
| | **TOTAL** | | **~76.000.000** |

### Konfigurasi AMD (Alternatif)

| No | Komponen | Spesifikasi | Harga (IDR) |
|----|----------|-------------|-------------|
| 1 | CPU | AMD Ryzen 9 7950X | 9.800.000 |
| 2 | GPU | NVIDIA RTX 4090 24GB | 32.000.000 |
| 3 | Motherboard | ASUS ROG Crosshair X670E Hero | 8.800.000 |
| 4 | RAM | G.Skill Trident Z5 64GB DDR5-6000 | 4.200.000 |
| 5 | Storage 1 | Samsung 990 Pro 2TB NVMe | 3.500.000 |
| 6 | Storage 2 | Samsung 870 EVO 2TB SATA | 2.800.000 |
| 7 | PSU | Seasonic PRIME TX-1300 | 5.200.000 |
| 8 | Cooler | Arctic Liquid Freezer II 360 | 2.200.000 |
| 9 | Case | Fractal Design Torrent | 2.800.000 |
| 10 | Fans | Included + Arctic P12 (3x) | 300.000 |
| | **TOTAL** | | **~71.600.000** |

---

## 💰 ALTERNATIF BUDGET - TIER STANDARD

**Target: Response Time 8-15 detik | Budget: ~35-45 Juta**

| No | Komponen | Spesifikasi | Harga (IDR) |
|----|----------|-------------|-------------|
| 1 | CPU | Intel Core i7-14700K | 7.200.000 |
| 2 | GPU | NVIDIA RTX 4070 Ti SUPER 16GB | 14.000.000 |
| 3 | Motherboard | ASUS TUF Gaming Z790-Plus WiFi | 4.500.000 |
| 4 | RAM | Kingston Fury Beast 32GB DDR5-5600 | 1.800.000 |
| 5 | Storage | Samsung 980 Pro 1TB NVMe | 1.800.000 |
| 6 | PSU | Corsair RM850x 850W | 2.000.000 |
| 7 | Cooler | DeepCool AK620 | 900.000 |
| 8 | Case | NZXT H7 Flow | 1.500.000 |
| | **TOTAL** | | **~33.700.000** |

---

## 🚀 ULTIMATE TIER - Maximum Performance

**Target: Response Time 1-3 detik | Budget: ~200 Juta**

| No | Komponen | Spesifikasi | Harga (IDR) |
|----|----------|-------------|-------------|
| 1 | CPU | AMD Threadripper PRO 7975WX (32C) | 45.000.000 |
| 2 | GPU | NVIDIA RTX 4090 x2 (NVLink) | 65.000.000 |
| 3 | Motherboard | ASUS Pro WS WRX90E-SAGE | 15.000.000 |
| 4 | RAM | 256GB DDR5-5600 ECC | 18.000.000 |
| 5 | Storage | Samsung PM9A3 3.84TB NVMe | 12.000.000 |
| 6 | PSU | Corsair AX1600i 1600W | 8.000.000 |
| 7 | Cooling | Custom Loop | 10.000.000 |
| 8 | Case | Caselabs/Custom | 5.000.000 |
| | **TOTAL** | | **~178.000.000** |

---

## ⚡ Performance Benchmarks (Estimated)

### Response Time by Configuration

| Hardware | Model | First Response | Cached Response |
|----------|-------|----------------|-----------------|
| CPU Only (i9-14900K) | Llama 3.2 3B | 25-40 detik | 0.1-0.5 detik |
| RTX 4070 Ti (16GB) | Llama 3.2 3B | 5-10 detik | 0.1-0.5 detik |
| RTX 4080 (16GB) | Llama 3.2 3B | 3-7 detik | 0.1-0.5 detik |
| RTX 4090 (24GB) | Llama 3.2 3B | 2-5 detik | 0.1-0.5 detik |
| RTX 4090 (24GB) | Mistral 7B | 4-8 detik | 0.1-0.5 detik |
| RTX 4090 x2 (48GB) | Llama 3.1 70B | 8-15 detik | 0.1-0.5 detik |

### Tokens per Second

| GPU | Model | Tokens/sec |
|-----|-------|------------|
| RTX 3060 12GB | Llama 3.2 3B | ~30 tok/s |
| RTX 4070 Ti 16GB | Llama 3.2 3B | ~80 tok/s |
| RTX 4080 16GB | Llama 3.2 3B | ~100 tok/s |
| RTX 4090 24GB | Llama 3.2 3B | ~150 tok/s |
| RTX 4090 24GB | Mistral 7B | ~60 tok/s |

---

## 🔧 Optimisasi Software

Dengan hardware di atas, tambahkan optimisasi ini:

### 1. Ollama GPU Settings
```bash
# Aktifkan semua GPU layers
OLLAMA_NUM_GPU=99

# Flash attention untuk kecepatan
OLLAMA_FLASH_ATTENTION=1

# Parallel requests
OLLAMA_NUM_PARALLEL=4
```

### 2. Redis Cache
- Cache hit rate 90%+ = response < 1 detik
- Alokasi RAM untuk Redis: 2-4GB

### 3. Model Selection
| Skenario | Model Recommended |
|----------|-------------------|
| Kecepatan prioritas | Llama 3.2 1B |
| Balanced | Llama 3.2 3B |
| Quality prioritas | Mistral 7B |
| Best quality | Llama 3.1 70B (butuh 48GB+ VRAM) |

---

## 📍 Toko Rekomendasi (Indonesia)

| Toko | Lokasi | Keunggulan |
|------|--------|------------|
| **Enterkomputer** | Jakarta, Online | Harga kompetitif, stok lengkap |
| **Tokopedia Official Store** | Online | Garansi resmi, banyak pilihan |
| **Shopee Mall** | Online | Promo/cashback |
| **Mangga Dua** | Jakarta | Nego langsung |
| **Hitech Mall** | Surabaya | Lengkap untuk Jawa Timur |

---

## ✅ Checklist Pembelian

- [ ] CPU dengan minimal 8 cores
- [ ] GPU NVIDIA dengan minimal 12GB VRAM
- [ ] RAM minimal 32GB DDR5
- [ ] NVMe SSD minimal 1TB
- [ ] PSU dengan headroom 200W+
- [ ] Cooling yang memadai
- [ ] UPS untuk stabilitas power

---

## 🎯 Kesimpulan

Untuk response time < 10 detik dengan budget optimal:

**REKOMENDASI UTAMA:**
- **GPU: NVIDIA RTX 4090 24GB** (~32 juta) - Ini yang PALING penting!
- **CPU: Intel i7-14700K** (~7 juta) - Cukup powerful
- **RAM: 64GB DDR5** (~4 juta) - Untuk headroom
- **Storage: 2TB NVMe** (~3.5 juta) - Kecepatan I/O

**Total investasi optimal: ~50-80 juta** untuk performa profesional.

GPU adalah investasi paling penting. RTX 4090 bisa membuat response 10-20x lebih cepat dibanding CPU only!
