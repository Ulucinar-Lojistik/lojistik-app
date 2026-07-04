import streamlit as st
import pandas as pd

st.set_page_config(page_title="Lojistik Sevkiyat Paneli", layout="wide")

# Sistem Hafızası (Session State) Kurulumları
if 'sevkiyatlar' not in st.session_state:
    st.session_state.sevkiyatlar = pd.DataFrame([
        {"MÜŞTERİ": "A101", "DEPO": "İZMİR", "ÜRÜNLER": "1.50 LT PET SU", "PLAKA": "15AB175", "DURUM": "PLAKA ATANDI"},
        {"MÜŞTERİ": "BİM", "DEPO": "KONYA", "ÜRÜNLER": "0.50 LT PET SU, 5.00 LT PET SU", "PLAKA": "", "DURUM": "BEKLİYOR (BOŞTA)"},
    ])
if 'sofor_listesi' not in st.session_state:
    st.session_state.sofor_listesi = ["İbrahim Erdem (15AB175)", "Hasan Akın (15AL283)"]
if 'depo_listesi' not in st.session_state:
    st.session_state.depo_listesi = ["A101 - İZMİR", "BİM - KONYA", "ABANT SU - BURDUR"]
if 'urun_listesi' not in st.session_state:
    st.session_state.urun_listesi = ["0.50 LT PET SU", "1.50 LT PET SU", "5.00 LT PET SU"]

# Mesaj hafızaları
if 'mesaj_sofor' not in st.session_state: st.session_state.mesaj_sofor = ""
if 'mesaj_depo' not in st.session_state: st.session_state.mesaj_depo = ""
if 'mesaj_urun' not in st.session_state: st.session_state.mesaj_urun = ""
if 'mesaj_genel' not in st.session_state: st.session_state.mesaj_genel = ""

def satir_boya(row):
    if str(row["PLAKA"]).strip() == "":
        return ['background-color: #fef7e0; color: #b06000; font-weight: bold;'] * len(row)
    else:
        return ['background-color: #e6f4ea; color: #137333; font-weight: 600;'] * len(row)

st.sidebar.markdown("### 🚪 SİSTEM GİRİŞİ")
giris_turu = st.sidebar.radio("Rolünüzü Seçin:", ["🚚 Şoför Ekranı (Sadece İzleme)", "⚙️ Yönetici Paneli (Veri Giriş)"])

# 📌 AKILLI SIRALAMA MANTIĞI: Plakası boş olanlar (bekleyenler) hep en üstte, atananlar en altta kalır.
if not st.session_state.sevkiyatlar.empty:
    st.session_state.sevkiyatlar['is_empty_plaka'] = st.session_state.sevkiyatlar['PLAKA'].apply(lambda x: 0 if str(x).strip() == "" else 1)
    st.session_state.sevkiyatlar = st.session_state.sevkiyatlar.sort_values(by=['is_empty_plaka']).reset_index(drop=True)
    st.session_state.sevkiyatlar = st.session_state.sevkiyatlar.drop(columns=['is_empty_plaka'])

if giris_turu == "🚚 Şoför Ekranı (Sadece İzleme)":
    st.markdown("<h2 style='text-align: center; color: #1e3d59;'>🚚 SEVKİYAT TAKİP VE AKTİF İŞ HAVUZU</h2>", unsafe_allow_html=True)
    st.markdown("<h5 style='text-align: center; color: #17b978;'>• CANLI ŞOFÖR BİLGİLENDİRME PANOSU •</h5>", unsafe_allow_html=True)
    st.divider()
    
    styled_df = st.session_state.sevkiyatlar.style.apply(satir_boya, axis=1)
    st.dataframe(styled_df, use_container_width=True, hide_index=True)
    st.markdown("<p style='text-align: center; color: #64748b; margin-top: 30px;'>🔄 Liste her dakika otomatik yenilenir. Boştaki (Turuncu) işler için sevkiyat amirliği ile görüşün.</p>", unsafe_allow_html=True)

else:
    st.title("⚙️ Lojistik Yönetici Kontrol Paneli")
    sifre = st.sidebar.text_input("Yönetici Şifresi:", type="password")
    
    if sifre == "1234":
        st.success("Giriş Başarılı. Veri ekleme ve güncelleme yapabilirsiniz.")
        
        if st.session_state.mesaj_sofor: st.success(st.session_state.mesaj_sofor); st.session_state.mesaj_sofor = ""
        if st.session_state.mesaj_depo: st.success(st.session_state.mesaj_depo); st.session_state.mesaj_depo = ""
        if st.session_state.mesaj_urun: st.success(st.session_state.mesaj_urun); st.session_state.mesaj_urun = ""
        if st.session_state.mesaj_genel: st.success(st.session_state.mesaj_genel); st.session_state.mesaj_genel = ""

        # GÜN SONU VE İŞ TEMİZLEME PANELİ
        st.divider()
        st.subheader("🧹 4. Gün Sonu Temizliği & İptal İşlemleri")
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            st.markdown("**🔄 Gün Sonu Sıfırlama**")
            st.caption("Plakası atanan (Yeşil) tüm işleri ekrandan temizler. Bekleyen (Turuncu) işler sonraki güne kalır.")
            if st.button("🗑️ Sadece 'PLAKA ATANDI' Olanları Listeden Temizle", type="secondary"):
                st.session_state.sevkiyatlar = st.session_state.sevkiyatlar[st.session_state.sevkiyatlar["DURUM"] == "BEKLİYOR (BOŞTA)"].reset_index(drop=True)
                st.session_state.mesaj_genel = "🧹 Plakası atanan tüm işler ekrandan temizlendi! Bekleyen işler ertesi güne devredildi."
                st.rerun()
                
        with col_g2:
            st.markdown("**❌ Özel İş İptal Et / Sil**")
            st.caption("İptal olan veya yanlış girilen herhangi bir iş emrini listeden tamamen kaldırır.")
            
            if not st.session_state.sevkiyatlar.empty:
                silme_secenekleri = []
                silme_haritasi = {}
                for list_idx, (real_idx, row) in enumerate(st.session_state.sevkiyatlar.iterrows()):
                    durum_notu = "✅" if row['DURUM'] == "PLAKA ATANDI" else "⏳"
                    opt_text = f"Sıra {list_idx+1}: {durum_notu} {row['MÜŞTERİ']} ({row['DEPO']}) -> {row['ÜRÜNLER']}"
                    silme_secenekleri.append(opt_text)
                    silme_haritasi[opt_text] = real_idx
                    
                secilen_silinecek = st.selectbox("Sistemden Tamamen Silinecek İşi Seçin:", silme_secenekleri, key="silme_box")
                if st.button("🚨 Seçilen İş Emrini Listeden Sil", type="primary"):
                    gercek_sil_idx = silme_haritasi[secilen_silinecek]
                    st.session_state.sevkiyatlar = st.session_state.sevkiyatlar.drop(gercek_sil_idx).reset_index(drop=True)
                    st.session_state.mesaj_genel = "❌ Seçilen iş emri başarıyla sistemden kaldırıldı!"
                    st.rerun()
            else:
                st.info("Listede silinebilecek aktif iş emri bulunmuyor.")

        # 🛠️ YENİ EKLENEN BÖLÜM: ARAÇ ARIZA / PLAKA REVİZE PANELİ
        st.divider()
        st.subheader("🔄 5. Atanan Plakayı İptal Et (Arıza / Revize)")
        st.caption("Araç arıza yaptığında veya müşteri ertelediğinde, plaka atanmış (Yeşil) bir işi tekrar 'Boşta/Bekliyor' (Turuncu) durumuna getirir.")
        
        # Sadece plakası dolu olanları filtrele
        atanmis_isler_df = st.session_state.sevkiyatlar[st.session_state.sevkiyatlar["PLAKA"] != ""]
        
        if not atanmis_isler_df.empty:
            revize_secenekleri = []
            revize_haritasi = {}
            for list_idx, (real_idx, row) in enumerate(atanmis_isler_df.iterrows()):
                rev_text = f"İş {list_idx+1}: {row['MÜŞTERİ']} ({row['DEPO']}) -> Araç: {row['PLAKA']}"
                revize_secenekleri.append(rev_text)
                revize_haritasi[rev_text] = real_idx
                
            col_r1, col_r2 = st.columns([2, 1])
            with col_r1:
                secilen_revize_is = st.selectbox("Plakası İptal Edilecek İşi Seçin:", revize_secenekleri)
            with col_r2:
                st.markdown("<div style='margin-top:28px;'></div>", unsafe_allow_html=True)
                if st.button("⚠️ Plakayı Sök / İşi Boşa Çıkar", use_container_width=True):
                    gercek_rev_idx = revize_haritasi[secilen_revize_is]
                    # Verileri eski haline çekiyoruz
                    st.session_state.sevkiyatlar.loc[gercek_rev_idx, "PLAKA"] = ""
                    st.session_state.sevkiyatlar.loc[gercek_rev_idx, "DURUM"] = "BEKLİYOR (BOŞTA)"
                    st.session_state.mesaj_genel = "🔄 Araç plakası iptal edildi, iş emri yeniden havuzun üst sırasına gönderildi!"
                    st.rerun()
        else:
            st.info("Şu anda plakası atanmış (Yeşil) aktif bir iş bulunmuyor.")

        st.divider()
        st.subheader("📦 1. Hızlı Tanımlamalar (Hafızaya Alınacak Sabitler)")
        col_s1, col_s2, col_s3 = st.columns(3)
        
        with col_s1:
            with st.form("sofor_ekleme_formu", clear_on_submit=True):
                st.markdown("**👤 Yeni Şoför & Plaka Kaydet**")
                s_ad = st.text_input("Şoför Adı Soyadı:")
                s_plaka = st.text_input("Araç Plakası:")
                if st.form_submit_button("💾 Şoförü Hafızaya Ekle"):
                    if s_ad and s_plaka:
                        st.session_state.sofor_listesi.append(f"{s_ad} ({s_plaka})")
                        st.session_state.mesaj_sofor = f"✅ Şoför {s_ad} ({s_plaka}) başarıyla hafızaya kaydedildi!"
                        st.rerun()
                        
        with col_s2:
            with st.form("depo_ekleme_formu", clear_on_submit=True):
                st.markdown("**🏢 Yeni Müşteri & Depo Kaydet**")
                m_ad = st.text_input("Müşteri / Firma Adı:")
                d_yer = st.text_input("Gideceği Yer/Şehir:")
                if st.form_submit_button("💾 Depoyu Hafızaya Ekle"):
                    if m_ad and d_yer:
                        st.session_state.depo_listesi.append(f"{m_ad} - {d_yer}")
                        st.session_state.mesaj_depo = f"✅ Depo {m_ad} - {d_yer} başarıyla hafızaya kaydedildi!"
                        st.rerun()

        with col_s3:
            with st.form("urun_ekleme_formu", clear_on_submit=True):
                st.markdown("**💧 Yeni Ürün Çeşidi Kaydet**")
                yeni_urun = st.text_input("Ürün Hacmi/Türü (Örn: 19 LT Damacana):")
                if st.form_submit_button("💾 Ürünü Hafızaya Ekle"):
                    if yeni_urun:
                        if yeni_urun not in st.session_state.urun_listesi:
                            st.session_state.urun_listesi.append(yeni_urun)
                            st.session_state.mesaj_urun = f"✅ Ürün {yeni_urun} başarıyla ürün listesine eklendi!"
                            st.rerun()
        
        st.divider()
        st.subheader("➕ 2. Günlük Yeni İş Emri Ekle")
        with st.form("is_formu", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1: 
                secilen_yer = st.selectbox("Müşteri & Depo Seç (Hafızadan):", st.session_state.depo_listesi)
            with c2: 
                secilen_urunler = st.multiselect("Yüklenecek Ürünleri Seçin (Çoklu Seçilebilir):", st.session_state.urun_listesi)
            
            if st.form_submit_button("🚀 Veriyi Havuza Gönder (Turuncu Yap)"):
                if secilen_yer and secilen_urunler:
                    if " - " in secilen_yer:
                        m_parca, d_parca = secilen_yer.split(" - ", 1)
                    else:
                        m_parca, d_parca = secilen_yer, "Belirtilmedi"
                        
                    urunler_metni = ", ".join(secilen_urunler)
                    
                    yeni_is = {
                        "MÜŞTERİ": m_parca, 
                        "DEPO": d_parca, 
                        "ÜRÜNLER": urunler_metni, 
                        "PLAKA": "", 
                        "DURUM": "BEKLİYOR (BOŞTA)"
                    }
                    st.session_state.sevkiyatlar = pd.concat([st.session_state.sevkiyatlar, pd.DataFrame([yeni_is])], ignore_index=True)
                    st.success("İş emri başarıyla havuza eklendi!")
                    st.rerun()
                else:
                    st.error("Lütfen listeden hem Depo hem de en az bir Ürün çeşidi seçin.")

        st.divider()
        st.subheader("✍️ 3. Boştaki İşe Plaka / Şoför Ata")
        
        bostaki_isler_df = st.session_state.sevkiyatlar[st.session_state.sevkiyatlar["PLAKA"] == ""]
        
        if not bostaki_isler_df.empty:
            bostaki_secenekler = []
            indeks_haritasi = {}
            
            for list_idx, (real_idx, row) in enumerate(bostaki_isler_df.iterrows()):
                gorunum_metni = f"İş Sırası {list_idx+1}: {row['MÜŞTERİ']} ({row['DEPO']}) -> {row['ÜRÜNLER']}"
                bostaki_secenekler.append(gorunum_metni)
                indeks_haritasi[gorunum_metni] = real_idx
                
            cc1, cc2 = st.columns(2)
            with cc1: 
                secilen_is_metni = st.selectbox("Plaka Atanacak İş Emrini Seçin:", bostaki_secenekler)
            with cc2: 
                secilen_sofor = st.selectbox("Atanacak Şoför & Araç (Hafızadan):", st.session_state.sofor_listesi)
            
            if st.button("✅ Plakayı Güncelle (Satırı Yeşile Döndür)"):
                if secilen_is_metni and secilen_sofor:
                    gercek_satir_no = indeks_haritasi[secilen_is_metni]
                    
                    if "(" in secilen_sofor:
                        plaka_ayikla = secilen_sofor.split("(")[1].replace(")", "")
                    else:
                        plaka_ayikla = secilen_sofor
                    
                    st.session_state.sevkiyatlar.loc[gercek_satir_no, "PLAKA"] = plaka_ayikla
                    st.session_state.sevkiyatlar.loc[gercek_satir_no, "DURUM"] = "PLAKA ATANDI"
                    st.success("Plaka başarıyla atandı!")
                    st.rerun()
        else:
            st.info("Havuzda plaka atanmayı bekleyen boşta iş yok.")
