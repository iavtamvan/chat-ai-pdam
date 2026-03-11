"""
API Integration Service - FINAL VERSION
Supports arrays in response template
"""

import re
import json
import httpx
from typing import Optional, Dict, Any, List
from pathlib import Path

DATA_FILE = Path("./data/api_integrations.json")


class APIIntegrationService:

    def __init__(self):
        print(f"✅ API Integration Service initialized")

    def _load_integrations(self) -> List[Dict]:
        print(f"📂 Loading from: {DATA_FILE.absolute()}")
        if DATA_FILE.exists():
            try:
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        active = [api for api in data if api.get('is_active', True)]
                        print(f"   Loaded {len(active)} active integrations")
                        return active
                    return []
            except Exception as e:
                print(f"❌ Error loading: {e}")
                return []
        return []

    def find_matching_api(self, message: str, integrations: List[Dict]) -> Optional[Dict]:
        message_lower = message.lower()

        for api in integrations:
            keywords = api.get('trigger_keywords', [])
            if isinstance(keywords, str):
                keywords = [k.strip() for k in keywords.split(',')]

            for keyword in keywords:
                if keyword.lower().strip() in message_lower:
                    print(f"✅ MATCH: '{keyword}' → '{api.get('name')}'")
                    return api

        return None

    def extract_params(self, message: str, api: Dict) -> Dict[str, str]:
        params = {}

        # Priority: Find numbers first
        numbers = re.findall(r'\b\d{6,12}\b', message)
        if numbers:
            params['no_pel'] = numbers[0]
            print(f"📝 Extracted no_pel={numbers[0]}")
            return params

        # Fallback patterns
        exclude_words = {'tagihan', 'cek', 'bayar', 'billing', 'tunggakan',
                         'pelanggan', 'info', 'data', 'lihat', 'berapa',
                         'tolong', 'minta', 'saya', 'nomor', 'air', 'pdam'}

        for param_def in api.get('params', []):
            name = param_def.get('name')
            pattern = param_def.get('pattern')

            if pattern and name and name not in params:
                try:
                    matches = re.findall(pattern, message)
                    for match in matches:
                        if match.lower() not in exclude_words:
                            params[name] = match
                            break
                except:
                    pass

        return params

    def build_url(self, api: Dict, params: Dict) -> str:
        url = api.get('url', '')
        for key, value in params.items():
            url = url.replace(f'{{{key}}}', str(value))
        return url

    def format_response(self, api: Dict, data: Any) -> str:
        """Format response - auto format untuk data PDAM"""
        # Always use auto format for best results
        return self._auto_format(data)

    def _format_currency(self, value) -> str:
        """Format number as currency"""
        if isinstance(value, (int, float)):
            return f"Rp {value:,.0f}".replace(",", ".")
        return str(value)

    def _auto_format(self, data: Dict) -> str:
        """Auto format dengan support untuk semua field termasuk arrays"""
        lines = []

        # Handle nested data
        if 'data' in data and isinstance(data['data'], dict):
            data = data['data']

        # ========== PELANGGAN ==========
        if 'pelanggan' in data and data['pelanggan']:
            p = data['pelanggan']
            lines.append("👤 **INFO PELANGGAN**")
            lines.append(f"━━━━━━━━━━━━━━━━━━━━")
            lines.append(f"No. Pelanggan : {p.get('nolangg', '-')}")
            lines.append(f"Nama          : {p.get('nama', '-')}")
            lines.append(f"Alamat        : {p.get('alamat', '-')}")
            lines.append(f"Kelurahan     : {p.get('kelurahan', '-')}")
            lines.append(f"Kecamatan     : {p.get('kecamatan', '-')}")
            lines.append(f"Cabang        : {p.get('cabang', '-')}")
            lines.append(f"Tarif         : {p.get('tarif', '-')}")
            lines.append(f"Status        : {p.get('status_ket', '-')}")

        # ========== TAGIHAN RUTIN ==========
        if 'rutin' in data and data['rutin']:
            r = data['rutin']
            lines.append("")
            lines.append(f"💰 **TAGIHAN BULAN INI** ({r.get('bulan_name', '')} {r.get('tahun', '')})")
            lines.append(f"━━━━━━━━━━━━━━━━━━━━")
            lines.append(f"Stand Lalu    : {r.get('stand_lalu', '-')}")
            lines.append(f"Stand Kini    : {r.get('stand_kini', '-')}")
            lines.append(f"Pemakaian     : {r.get('pemakaian', '-')}")
            lines.append(f"Tagihan       : {self._format_currency(r.get('tagihan', 0))}")
            lines.append(f"Status        : {r.get('status_rekening', '-')}")
            if r.get('tanggal_bayar') and r.get('tanggal_bayar') != '-':
                lines.append(f"Tgl Bayar     : {r.get('tanggal_bayar', '-')}")
                lines.append(f"Tempat Bayar  : {r.get('tempat_bayar', '-')}")

        # ========== TUNGGAKAN (ARRAY) ==========
        if 'tunggakan' in data and data['tunggakan'] and len(data['tunggakan']) > 0:
            lines.append("")
            lines.append("⚠️ **TUNGGAKAN**")
            lines.append(f"━━━━━━━━━━━━━━━━━━━━")

            total_tunggakan = 0
            for i, t in enumerate(data['tunggakan'], 1):
                tagihan = t.get('tagihan', 0)
                total_tunggakan += tagihan if isinstance(tagihan, (int, float)) else 0

                periode = f"{t.get('bulan_name', '')} {t.get('tahun', '')}"
                lines.append(f"{i}. {periode}")
                lines.append(f"   Pemakaian: {t.get('pemakaian', '-')}")
                lines.append(f"   Tagihan  : {self._format_currency(tagihan)}")

            if total_tunggakan > 0:
                lines.append(f"")
                lines.append(f"📊 Total Tunggakan: {self._format_currency(total_tunggakan)}")

        # ========== SUPLISI (ARRAY) ==========
        if 'suplisi' in data and data['suplisi'] and len(data['suplisi']) > 0:
            lines.append("")
            lines.append("🔧 **TAGIHAN SUPLISI**")
            lines.append(f"━━━━━━━━━━━━━━━━━━━━")

            for i, s in enumerate(data['suplisi'], 1):
                lines.append(f"{i}. {s.get('jenis', s.get('keterangan', 'Suplisi'))}")
                lines.append(f"   Tagihan: {self._format_currency(s.get('tagihan', s.get('jumlah', 0)))}")
                if s.get('status'):
                    lines.append(f"   Status : {s.get('status')}")

        # ========== ANGSURAN REKENING (ARRAY) ==========
        if 'angsuran_rek' in data and data['angsuran_rek'] and len(data['angsuran_rek']) > 0:
            lines.append("")
            lines.append("📅 **ANGSURAN REKENING**")
            lines.append(f"━━━━━━━━━━━━━━━━━━━━")

            for i, a in enumerate(data['angsuran_rek'], 1):
                lines.append(f"{i}. Angsuran ke-{a.get('angsuran_ke', i)}")
                lines.append(f"   Jumlah : {self._format_currency(a.get('jumlah', a.get('tagihan', 0)))}")
                lines.append(f"   Status : {a.get('status', 'Belum Lunas')}")

        # ========== FLAT (ARRAY) ==========
        if 'flat' in data and data['flat'] and len(data['flat']) > 0:
            lines.append("")
            lines.append("📋 **TAGIHAN FLAT**")
            lines.append(f"━━━━━━━━━━━━━━━━━━━━")

            for i, f in enumerate(data['flat'], 1):
                lines.append(f"{i}. {f.get('keterangan', f.get('jenis', 'Flat'))}")
                lines.append(f"   Tagihan: {self._format_currency(f.get('tagihan', f.get('jumlah', 0)))}")

        # ========== SUMMARY ==========
        if lines:
            # Calculate total if possible
            total = 0
            if 'rutin' in data and data['rutin']:
                rutin_tag = data['rutin'].get('tagihan', 0)
                if isinstance(rutin_tag, (int, float)) and not data['rutin'].get('is_terbayar', False):
                    total += rutin_tag

            if 'tunggakan' in data:
                for t in data.get('tunggakan', []):
                    tag = t.get('tagihan', 0)
                    if isinstance(tag, (int, float)):
                        total += tag

            if total > 0:
                lines.append("")
                lines.append("━━━━━━━━━━━━━━━━━━━━")
                lines.append(f"💵 **TOTAL TAGIHAN: {self._format_currency(total)}**")

            return "\n".join(lines)

        # Fallback
        return json.dumps(data, indent=2, ensure_ascii=False)

    async def call_api(self, api: Dict, params: Dict) -> Dict[str, Any]:
        url = self.build_url(api, params)
        method = api.get('method', 'GET').upper()

        headers = api.get('headers', {})
        if isinstance(headers, list):
            headers = {h['key']: h['value'] for h in headers if h.get('key')}

        print(f"🌐 Calling: {method} {url}")

        try:
            async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
                resp = await client.request(method=method, url=url, headers=headers)

                print(f"📥 Status: {resp.status_code}")

                if resp.status_code == 200:
                    try:
                        data = resp.json()
                    except:
                        data = {"raw": resp.text}

                    return {
                        "success": True,
                        "data": data,
                        "formatted": self.format_response(api, data),
                        "api_name": api.get('name')
                    }
                else:
                    return {
                        "success": False,
                        "error": f"API returned {resp.status_code}",
                        "api_name": api.get('name')
                    }
        except Exception as e:
            return {"success": False, "error": str(e), "api_name": api.get('name')}

    async def process_message(self, message: str) -> Optional[Dict]:
        integrations = self._load_integrations()

        if not integrations:
            return None

        api = self.find_matching_api(message, integrations)
        if not api:
            return None

        params = self.extract_params(message, api)
        print(f"📝 Params: {params}")

        url = api.get('url', '')
        required = re.findall(r'\{(\w+)\}', url)
        missing = [p for p in required if p not in params]

        if missing:
            return {
                "success": False,
                "needs_param": True,
                "api_name": api.get('name'),
                "message": "Mohon sertakan nomor pelanggan. Contoh: cek tagihan 07600026"
            }

        return await self.call_api(api, params)


def get_api_integration_service() -> APIIntegrationService:
    return APIIntegrationService()