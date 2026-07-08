import streamlit as st
import pandas as pd
import requests
import json
    
# Sayfa Genişlik Ayarı
st.set_page_config(layout="wide", page_title="Lojistik Yönetici Kontrol Paneli")

# Çalışan Apps Script URL'niz
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzh13LuC19Y-4vzTldvQYnJc-Qs1P_y02Yk7wU_-d6sC7kMYp5poEzkpaDftEFJVx05ZQ/exec"

# --- DİNAMİK VERİ ÇEKME FONKSİYONLARI ---
def veri_cek():
    try:
        response = requests.get(SCRIPT_URL, timeout=10)
        if response.status_code == 200:
            veri = response.json()
            if veri and isinstance(veri, list) and len(veri) > 0:
                df = pd.DataFrame(veri)
                df.columns = [str(c).strip().upper() for c in df.columns]
                if "MÜŞTERI" in df.columns:
                    df.rename(columns={"MÜŞTERI": "MÜŞTERİ"}, inplace=True)
                return df
    except:
        pass
    return pd.DataFrame(columns=["MÜŞTERİ", "DEPO", "ÜRÜNLER", "PLAKA", "DURUM"])

def veri_gonder(action, row_data, search_key=None):
    payload = {
        "sheetName": "Sayfa1",
        "action": action,
        "rowData": row_data,
        "searchKey": search_key
    }
    try:
        response = requests.post(SCRIPT_URL, data=json.dumps(payload), headers={"Content-Type": "application/json"}, timeout=10)
        return response.status_code == 200
    except:
        return False

# İlk açılışta verileri hafızaya al
if 'sevkiyatlar' not in st.session_state:
    st.session_state.sevkiyatlar = veri_cek()

# --- LİSTE VE TANIMLAMA HAFIZASI (MÜKERRER KONTROLLÜ) ---
if 'soforler' not in st.session_state:
    st.session_state.soforler = ["Abant (15abnt15)", "Hüseyin (15hsyn15)", "Selim (15slm15)"]
if 'musteriler' not in st.session_state:
    st.session_state.musteriler = ["ABANT FABRİKA - BURDUR - AĞLASUN", "Abant Burdur - Burdur", "Burdur Belediye - Burdur"]
if 'urunler' not in st.session_state:
    st.session_state.urunler = ["0.33 LT EURO", "0.33 LT PALEX", "0.5 LT EURO", "0.5 LT PALEX", "1.5 LT EURO", "5 LT", "19 LT PC DAMACANA", "19 LT CAM DAMACANA", "SEPARATÖR KARTON - 5 LT"]

# --- VERİ YÜKLE VE SIRALA ---
df_aktif = st.session_state.sevkiyatlar.copy()

for col in ["MÜŞTERİ", "DEPO", "ÜRÜNLER", "PLAKA", "DURUM"]:
    if col not in df_aktif.columns:
        df_aktif[col] = ""
    df_aktif[col] = df_aktif[col].fillna("").astype(str).str.strip()

# 🔥 YENİ SIRALAMA: Bekleyenler (BEKLİYOR) her zaman en üstte
if not df_aktif.empty:
    # Durum içinde 'BEKLİYOR' geçenlere 0, diğerlerine 1 puanı veriyoruz
    df_aktif["SIRALAMA_PUANI"] = df_aktif["DURUM"].apply(lambda x: 0 if "BEKLİYOR" in str(x).upper() else 1)
    
    # Puanı küçük olan (0 yani Bekliyor) yukarı, sonra müşteri adına göre alfabetik sırala
    df_aktif = df_aktif.sort_values(by=["SIRALAMA_PUANI", "MÜŞTERİ"]).drop(columns=["SIRALAMA_PUANI"]).reset_index(drop=True)

gercek_kayit_var = len(df_aktif) > 0 and df_aktif.iloc[0]["MÜŞTERİ"] != ""

# --- 📌 SOL MENÜ (SİSTEM GİRİŞİ) ---
st.sidebar.title("🗂️ SİSTEM GİRİŞİ")
rol_secimi = st.sidebar.radio(
    "Rolünüzü Seçin:",
    ["🚚 Şoför Ekranı (Sadece İzleme)", "⚙️ Yönetici Paneli (Veri Giriş)"],
    key="rol_secimi_key"
)

yonetici_izni = False
if "⚙️ Yönetici Paneli" in rol_secimi:
    sifre = st.sidebar.text_input("Yönetici Şifresi:", type="password", key="yonetici_sifre_key")
    if sifre == "1234":  # Şifreyi fabrika standardı olarak 1234 bıraktım
        st.sidebar.success("Yönetici Girişi Başarılı.")
        yonetici_izni = True
    elif sifre != "":
        st.sidebar.error("Hatalı Şifre!")
else:
    yonetici_izni = False

# --- 📊 ANA TABLO GÖSTERİMİ (HER İKİ ROLDE DE EN ÜSTTE GÖRÜNÜR) ---
st.title("🚚 ULUÇINAR KARAYOLU YÜK TAŞIMA KOOPERATİFİ İŞ TAKİP HAVUZU")

if gercek_kayit_var:
    def satir_renklendir(row):
        if str(row.get('DURUM', '')).upper() == 'PLAKA ATANDI':
            return ['background-color: #d4edda; color: #155724; font-weight: bold;'] * len(row)
        else:
            return ['background-color: #fff3cd; color: #856404; font-weight: bold;'] * len(row)
    st.dataframe(df_aktif[["MÜŞTERİ", "DEPO", "ÜRÜNLER", "PLAKA", "DURUM"]].style.apply(satir_renklendir, axis=1), use_container_width=True)
else:
    st.info("Şu anda aktif iş havuzunda gösterilecek kayıt yok. Lütfen aşağıdan yeni iş emri ekleyin.")

 # --- 🔒 YÖNETİCİ PANELİ İÇERİĞİ ---
if "⚙️ Yönetici Paneli" in rol_secimi and yonetici_izni:
    st.markdown("---")
    st.header("⚙️ Lojistik Yönetici Kontrol Paneli")
    
    # --- 🏢 SABİT TANIMLAMALAR (EKLEME) ---
 st.subheader("📋 Sabit Tanımlamalar")
 col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**🚚 Şoför İşlemleri**")
    y_sof = st.text_input("Şoför Adı (Plaka):")
    if st.button("Şoförü Kaydet"):
        if y_sof and y_sof not in st.session_state.soforler:
            st.session_state.soforler.append(y_sof)
            st.rerun()

with col2:
    st.markdown("**🗺️ Müşteri İşlemleri**")
    y_mus = st.text_input("Müşteri Adı - Depo:")
    if st.button("Müşteriyi Kaydet"):
        if y_mus and y_mus not in st.session_state.musteriler:
            st.session_state.musteriler.append(y_mus)
            st.rerun()

with col3:
    st.markdown("**📦 Ürün İşlemleri**")
    y_urn = st.text_input("Ürün Adı:")
    if st.button("Ürünü Kaydet"):
        if y_urn and y_urn not in st.session_state.urunler:
            st.session_state.urunler.append(y_urn)
            st.rerun()
st.markdown("---")
 # --- 🗑️ SİLME İŞLEMLERİ ---
 st.subheader("🗑️ Kayıtlı Tanımlamaları Sil")

 col_s1, col_s2, col_s3 = st.columns(3)
 
 with col_s1:
     s_sof = st.selectbox("Silinecek Şoför:", [""] + st.session_state.soforler)
     if st.button("Şoförü Sil"):
         if s_sof in st.session_state.soforler:
             st.session_state.soforler.remove(s_sof)
 with col_s2:
     s_mus = st.selectbox("Silinecek Müşteri:", [""] + st.session_state.musteriler)
     if st.button("Müşteriyi Sil"):
         if s_mus in st.session_state.musteriler:
             st.session_state.musteriler.remove(s_mus)
 with col_s3:
     s_urn = st.selectbox("Silinecek Ürün:", [""] + st.session_state.urunler)
     if st.button("Ürünü Sil"):
         if s_urn in st.session_state.urunler:
             st.session_state.urunler.remove(s_urn)

 st.markdown("---")
   
    # --- 🧼 GÜN SONU TEMİZLİĞİ VE TEKLİ İŞ SİLME ---
    st.subheader("🧹 Gün Sonu Temizliği & İş İptal Etme")
    
    col_temiz1, col_temiz2 = st.columns(2)
    
    # SOL SÜTUN: Tamamlananları toplu temizleme (Burası aynı kalıyor)
    with col_temiz1:
        st.markdown("**🧼 Tamamlanan İşleri Temizle**")
        if st.button("🧼 Sadece 'PLAKA ATANDI' Olanları Listeden Temizle", key="btn_gun_sonu"):
            if gercek_kayit_var:
                atananlar = df_aktif[df_aktif['DURUM'].str.upper() == 'PLAKA ATANDI']
                if not atananlar.empty:
                    silinen_sayisi = 0
                    with st.spinner("Tamamlanan işler temizleniyor..."):
                        for _, r in atananlar.iterrows():
                            silinecek_satir = ["", "", str(r['ÜRÜNLER']), "", ""]
                            if veri_gonder("SIL", silinecek_satir, search_key=str(r['ÜRÜNLER'])):
                                silinen_sayisi += 1
                    st.success(f"Tamamlanmış {silinen_sayisi} adet sevkiyat havuzdan temizlendi!")
                    st.session_state.sevkiyatlar = veri_cek()
                    st.rerun()
                else:
                    st.info("Temizlenecek 'PLAKA ATANDI' durumunda iş bulunamadı.")
            else:
                st.info("Havuzda temizlenecek kayıt yok.")

    # SAĞ SÜTUN: İŞTE YENİ YAPTIĞIMIZ TEKLİ SEÇİP SİLME ALANI
    with col_temiz2:
        st.markdown("**❌ İptal Olan Boştaki İşi Tekli Sil**")
        
        # Sadece DURUM'u "BEKLİYOR" olan işleri filtreleyip listeliyoruz
        bostakiler_liste = df_aktif[df_aktif['DURUM'].str.contains("BEKLİYOR", na=False)]
        
        if not bostakiler_liste.empty:
            # Kullanıcının ekranda rahatça görebilmesi için "Müşteri - Ürün" şeklinde seçenek listesi hazırlıyoruz
            secenekler = [f"{r['MÜŞTERI' if 'MÜŞTERI' in df_aktif.columns else 'MÜŞTERİ']} -> {r['ÜRÜNLER']}" for idx, r in bostakiler_liste.iterrows()]
            
            # Seçeneklerin hangi satır indeksine denk geldiğini arkada eşleştiriyoruz
            secenek_haritasi = {f"{r['MÜŞTERI' if 'MÜŞTERI' in df_aktif.columns else 'MÜŞTERİ']} -> {r['ÜRÜNLER']}": r for idx, r in bostakiler_liste.iterrows()}
            
            # Kullanıcı listeden iptal olan işi seçer
            secilen_iptal_is = st.selectbox("İptal Olan/Silinecek Boştaki İşi Seçin:", secenekler, key="sil_tekli_bosta_sec")
            
            if st.button("🗑️ Seçili İşi Havuzdan Sil (İptal Et)", key="btn_bosta_tekli_sil"):
                # Seçilen işin satır verisini haritadan çekiyoruz
                iptal_satir = secenek_haritasi[secilen_iptal_is]
                silinecek_satir = ["", "", str(iptal_satir['ÜRÜNLER']), "", ""]
                
                with st.spinner("Seçili iş siliniyor..."):
                    # Google Sheets'e sadece bu işin ÜRÜNLER anahtarını göndererek sildiriyoruz
                    if veri_gonder("SIL", silinecek_satir, search_key=str(iptal_satir['ÜRÜNLER'])):
                        st.success(f"'{secilen_iptal_is}' işi başarıyla havuzdan silindi!")
                        st.session_state.sevkiyatlar = veri_cek()
                        st.rerun()
                    else:
                        st.error("Silme işlemi sırasında bir hata oluştu.")
        else:
            st.info("Havuzda iptal edilebilecek (BEKLİYOR durumunda) boşta iş yok.")
   
    # --- ➕ GÜNLÜK YENİ İŞ EMRİ EKLE ---
    st.subheader("➕ Günlük Yeni İş Emri Ekle")
    col_e1, col_e2 = st.columns(2)
    with col_e1:
        secilen_secenek = st.selectbox("Müşteri & Depo Seç:", st.session_state.musteriler, key="y_isl_mus")
    with col_e2:
        secilen_urunler = st.multiselect("Yüklenecek Ürünleri Seçin:", st.session_state.urunler, key="y_isl_urn")
        
    if st.button("🚀 Veriyi Havuza Gönder (Turuncu Yap)", key="btn_isl_ekle"):
        if not secilen_urunler:
            st.error("Lütfen en az bir ürün seçin!")
        else:
            parcalar = secilen_secenek.split(" - ")
            musteri = parcalar[0]
            depo = parcalar[1] if len(parcalar) > 1 else parcalar[0]
            urunler_str = ", ".join(secilen_urunler)
            
            yeni_satir = [musteri, depo, urunler_str, "", "BEKLİYOR (BOŞTA)"]
            with st.spinner("Havuza ekleniyor..."):
                if veri_gonder("EKLE", yeni_satir):
                    st.success("İş emri başarıyla havuza gönderildi!")
                    st.session_state.sevkiyatlar = veri_cek()
                    st.rerun()
                else:
                    st.error("E-tabloya yazma hatası oluştu.")

    st.markdown("---")

    # --- ✍️ BOŞTAKİ İŞE PLAKA / ŞOFÖR ATA ---
    st.subheader("✍️ Boştaki İşe Plaka / Şoför Ata")
    bosta_olanlar = df_aktif[df_aktif['PLAKA'] == ""] if gercek_kayit_var else pd.DataFrame()
    
    if not bosta_olanlar.empty:
        is_secenekleri = [f"Sıra {idx+1}: {r['MÜŞTERI' if 'MÜŞTERI' in df_aktif.columns else 'MÜŞTERİ']} -> {r['ÜRÜNLER']}" for idx, r in bosta_olanlar.iterrows()]
        idx_haritasi = {f"Sıra {idx+1}: {r['MÜŞTERI' if 'MÜŞTERI' in df_aktif.columns else 'MÜŞTERİ']} -> {r['ÜRÜNLER']}": idx for idx, r in bosta_olanlar.iterrows()}
        
        col_a1, col_a2 = st.columns(2)
        with col_a1:
            secilen_is = st.selectbox("Plaka Atanacak İş Emrini Seçin:", is_secenekleri, key="ata_is_sel")
        with col_a2:
            secilen_arac = st.selectbox("Atanacak Şoför & Araç:", st.session_state.soforler, key="ata_sof_sel")
            
        if st.button("✅ Plakayı Güncelle (Satırı Yeşile Döndür)", key="btn_ata_kaydet"):
            g_idx = idx_haritasi[secilen_is]
            plaka = secilen_arac.split("(")[-1].replace(")", "").strip()
            
            guncel_satir = [
                str(df_aktif.loc[g_idx, "MÜŞTERİ"]), 
                str(df_aktif.loc[g_idx, "DEPO"]), 
                str(df_aktif.loc[g_idx, "ÜRÜNLER"]), 
                str(plaka), 
                "PLAKA ATANDI"
            ]
            with st.spinner("Plaka atanıyor..."):
                if veri_gonder("GUNCELLE", guncel_satir, search_key=df_aktif.loc[g_idx, "ÜRÜNLER"]):
                    st.success("Plaka ataması başarıyla tamamlandı!")
                    st.session_state.sevkiyatlar = veri_cek()
                    st.rerun()
    else:
        st.info("Şu anda plaka atanmayı bekleyen boşta iş yok.")

    st.markdown("---")

    # --- 📝 AKTİF İŞ EMRİNİ DÜZENLE / DÜZELT ---
    st.subheader("📝 Aktif İş Emrini Düzenle / Düzelt")
    if gercek_kayit_var:
        duzenleme_secenekleri = [f"Sıra {idx+1}: {r['MÜŞTERİ']} ({r['DURUM']})" for idx, r in df_aktif.iterrows()]
        d_idx_haritasi = {f"Sıra {idx+1}: {r['MÜŞTERİ']} ({r['DURUM']})": idx for idx, r in df_aktif.iterrows()}
        secilen_duzenleme = st.selectbox("Düzenlenecek İş Emrini Seçin:", duzenleme_secenekleri, key="duz_is_sel")
        g_d_idx = d_idx_haritasi[secilen_duzenleme]
        
        col_d1, col_d2, col_d3 = st.columns(3)
        with col_d1:
            yeni_m = st.text_input("Müşteri Adı:", value=df_aktif.loc[g_d_idx, "MÜŞTERİ"], key="duz_m_in")
        with col_d2:
            yeni_d = st.text_input("Depo Adı:", value=df_aktif.loc[g_d_idx, "DEPO"], key="duz_d_in")
        with col_d3:
            yeni_p = st.text_input("Plaka:", value=df_aktif.loc[g_d_idx, "PLAKA"], key="duz_p_in")
            
        if st.button("💾 Değişiklikleri Kaydet", key="btn_duz_kaydet"):
            y_durum = "PLAKA ATANDI" if yeni_p.strip() != "" else "BEKLİYOR (BOŞTA)"
            guncel_satir = [yeni_m, yeni_d, df_aktif.loc[g_d_idx, "ÜRÜNLER"], yeni_p, y_durum]
            with st.spinner("Değişiklikler güncelleniyor..."):
                if veri_gonder("GUNCELLE", guncel_satir, search_key=df_aktif.loc[g_d_idx, "ÜRÜNLER"]):
                    st.success("İş emri revize edildi!")
                    st.session_state.sevkiyatlar = veri_cek()
                    st.rerun()
    else:
        st.info("Düzenlenecek herhangi bir aktif iş emri bulunmuyor.")

elif "⚙️ Yönetici Paneli" in rol_secimi and not yonetici_izni:
    st.warning("Yönetici işlemlerini görebilmek için lütfen sol menüden şifrenizi girin.")
else:
    st.info("💡 Şu anda Şoför modundasınız. Yukarıdaki tablodan anlık atamaları izleyebilirsiniz. Veri girişi ve düzenleme yapmak için sol menüden 'Yönetici Paneli' seçeneğine geçip şifrenizi girmeniz gerekmektedir.")
