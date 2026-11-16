"""Availability register: evidence of an inquiry route is not evidence of access."""
from pathlib import Path
import json

HERE = Path(__file__).resolve().parent


def main():
    sources = {r['id']:r for r in json.loads((HERE/'SOURCE_MANIFEST.json').read_text())}
    definitions = [
        ('J01','従来人手ルート作成時間の公表範囲','日本郵便担当者・オプティマインド',['JP_LOOGIA'],'PUBLIC',
         'HTMLの公開本文を実取得。熟練者/新人の報告範囲を秒へ換算。','ゆうパック試行地域。個別拠点未記載。','記事は2021年時点、測定期間未記載。','秒/当該担当者のルート作成業務',
         '限定的な出典付き引用・数値換算。原ログのオープンライセンス未確認。','原ログなし。記載範囲に個人住所はない。標本・N/V不明。',
         {'D':False,'W':False,'T_external':True,'T_common':False},'既取得。詳細な原記録の提供期間は不明。'),
        ('J02','従来人手対照群・便別距離/訪問順/計画時刻の元記録','日本郵便・オプティマインド・CBcloud。実際の保管/承認主体は要確認。',['JP_2020_RELEASE','JP_2020_APPENDIX','JP_2019_OPTIMIND','OPTIMIND_2020','OPTIMIND_2021','CB_2021_RELEASE'],'UNVERIFIED',
         '日本郵便で担当・保管・集計可否を照会、オプティマインドで事例条件を確認。未送信。','全国の一部試行地域。特定データの地域は未確認。','2018〜2021年の実証文脈。対象原記録の期間/現存は未確認。','車両日/便/計画セッションを希望。現存単位は未確認。',
         '研究利用・再提供・掲載・費用・契約の要否は未確認。','元データは顧客/車両/営業情報を含み得る。最初は住所/GPSなしの提供側集計。',
         {'D':None,'W':None,'T_external':None,'T_common':None},'研究側の依頼準備1〜2営業日見積。回答・許諾・抽出は不明。'),
        ('J03','新東京郵便局の入退場・荷待ち/荷役実証原記録','日本郵便・Hacobu・Safie/Kix。保管/承認主体は要確認。',['SAFIE_JP_2024','HACOBU_JP_2024'],'UNVERIFIED',
         '日本郵便へ取次/許可主体、Hacobuへ記録辞書・出庫区分・保管・集計可否を照会。','新東京郵便局。大田区/京浜・ToC出庫との一致を確認していない。','公表実証期間2024-10-01〜2024-12-31。現在の保管未確認。','車両入退場/荷待ち/荷役イベント。研究readyイベントは未確認。',
         '研究提供条件・契約要否・ライセンスは未確認。','車番/映像は初回依頼から除く。到着バースの入庫待ちを出庫Wにしない。',
         {'D':False,'W':None,'T_external':False,'T_common':False},'実証説明は既取得。原記録提供までの日数は不明。'),
        ('J04','P-DX配達経歴/再配達率の限定用途提供データ','日本郵便。公表された協力企業向け。',['JP_PDX_DATA'],'UNVERIFIED',
         '公開ページの列/加工/用途限定を取得。研究の別用途提供は新たに確認が必要。','世田谷局・柏局・板橋西局の担当地域。','元の観測期間は対象ページで未確定。月単位集計。','丁目/月の再配達多寡。原配達経歴とは別。',
         '公表された提供は特定の取り組みのみ。研究者への提供・転用許可は未確認。','元の追跡番号/住所は要求せず、少数地域秘匿の集計を原記録へ戻さない。',
         {'D':False,'W':False,'T_external':False,'T_common':False},'説明は既取得。別目的の研究利用の期間は不明。'),
        ('J05','日本郵便の全国走行規模推計の公開スライド','日本郵便が説明、東京都TDPFが公開。',['TOKYO_JP_DATA'],'PUBLIC',
         'PDF全体と該当p.164を取得、図を目視。','日本全国、2輪/軽4輪等。','2024年3月の掲載URL。推計の対象年度は未確認。','km/年という推計規模。',
         'スライドは日本郵便の著作権表示あり。公開閲覧を原記録のオープンライセンスとしない。','集計規模のみ。人手/AI、ToC/他業務、拠点別の分離なし。',
         {'D':False,'W':False,'T_external':False,'T_common':False},'公開資料は今回取得済み。元データの追加提供期間は不明。'),
        ('J06','日本郵政ESG環境の会社/年度集計','日本郵政グループ',['JP_GROUP_ENV'],'PUBLIC',
         '公式HTML表を取得。CO2/km原単位等を確認。','会社/グループ全体。','2019・2021〜2025年度等の掲載表。','t-CO2/km等。配送計画のkmではない。',
         '出典付き背景参照。原データの研究利用/再配布条件は未確認。','拠点/日/便/計画方式の特定不可。排出量の割算で対象外Dを作らない。',
         {'D':False,'W':False,'T_external':False,'T_common':False},'公開表は取得済み。対象運行原記録への提供経路は不明。'),
        ('J07','西米良村共同集配の原著論文','日本工営・西米良村・九州工業大学等',['NISHIMERA_PAPER','NISHIMERA_LANDING','NISHIMERA_AUTHOR'],'PUBLIC',
         '原著PDF・書誌・電子付録0件を確認。元データ申請要項未確認。','宮崎県西米良村、小川地区等。','原著2019年、2015〜2016年等の実証文脈。','共同集配の調査/調整/コスト積算。',
         '©交通工学研究会。フリー閲覧と原データ二次利用を区別。','3社・貨客混載。A/B/C社の日本郵便への同定と元調査の再利用未確認。',
         {'D':False,'W':False,'T_external':False,'T_common':False},'論文は取得済み。元調査記録の提供までの期間は不明。'),
        ('J08','集配用バイク・インフラ管理実証の画像/位置原記録','日本郵政・日本郵便・NTT東日本/NTT ME',['NTT_JP_2026'],'UNVERIFIED',
         '実証の公式発表を取得。原記録の公開/研究申請は未確認。','実証地域の位置情報。一般配送車ToCとは別。','2026-11-04〜11-10予定。終了/成果の確認はない。','バイク画像/位置の観測。',
         '第三者研究利用・提供条件は未確認。','画像/位置を含む。2輪距離を一般配送車のDにしない。',
         {'D':False,'W':False,'T_external':False,'T_common':False},'発表は取得済み。原記録取得の期間は不明。'),
        ('J09','国交省の荷待ち・物流統計公開資料','国土交通省',['MLIT_WAIT_SURVEY','MLIT_WAIT_DX','MLIT_CENSUS'],'PUBLIC',
         'PDF/統計ページを取得。対象・定義を確認。','一般貨物・全国等。日本郵便単独の手動ToCではない。','2025年度調査、2025年3月DX報告、2021年センサス等。','一般貨物の運行/集計統計。',
         '出典を示して背景資料として参照。個票の提供制度を目的原記録の取得制度としない。','集計/匿名事例。日本郵便D/W/Tの対応不能。',
         {'D':False,'W':False,'T_external':False,'T_common':False},'公開資料は取得済み。日本郵便対象原記録の経路・期間は不明。'),
        ('J10','JP Innovation Program募集・地理空間テーマ','日本郵便',['JP_INNOVATION','JP_INNOVATION_THEME','JP_INNOVATION_CONTACT'],'PUBLIC',
         '募集・資格・公式問い合わせを取得。研究データの申請は行わない。','日本郵便データ等を利用したスタートアップ共創。','現行公開募集条件。選考時期はデータ提供時期と別。','事業提案/共創。D/W/Tデータ一覧はない。',
         '法人・2名以上・既存主力サービス等の応募要件。研究者のデータ申請資格は未確認。','データ加工・収益化のテーマであり、誰でも利用できる研究原記録ではない。',
         {'D':False,'W':False,'T_external':False,'T_common':False},'要項は取得済み。選考翌月末目途を研究用データのSLAにしない。'),
    ]
    records=[]
    for row in definitions:
        rid,name,holder,ids,status,method,region,period,unit,license_note,constraints,metrics,lead=row
        records.append({'id':rid,'data_name':name,'holder_or_publisher':holder,'source_ids':ids,
                        'urls':[sources[s]['url'] for s in ids], 'acquisition_method':method,
                        'license_and_conditions':license_note,'privacy_and_commercial_constraints':constraints,
                        'region':region,'period':period,'unit':unit,'metric_computability_now':metrics,
                        'lead_time_and_basis':lead,'provider_promised_days':None,'final_status':status,
                        'raw_target_access_status':'PUBLIC' if rid=='J01' else 'UNVERIFIED',
                        'general_contact_is_not_permission':True})
    output={'version':'JP-A-acquisition-v1.0','date':'2026-11-11',
            'allowed_statuses':['PUBLIC','REQUESTABLE','NEGOTIATION_REQUIRED','UNVERIFIED','UNAVAILABLE'],
            'records':records,'human_T_references_s':{'experienced':[300,600],'novice':[1800,3600]},
            'Japan_Post_human_plan_D_km':None,'Japan_Post_loading_W_min':None,'Japan_Post_common_T_s':None,
            'level_1_all_three':'HOLD','level_1_T_only':'CONDITIONAL GO','level_2':'HOLD','level_3':'HOLD',
            'outbound_contact_executed':False,'form_submission_executed':False,'alternative_adopted':False,
            'researcher_followup_business_days':[5,10,20], 'followup_days_are_provider_SLA':False}
    (HERE/'DATA_AVAILABILITY_REGISTER.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
    print('10 data/source records registered; target raw D/W/T access is unverified; T reported range is public')


if __name__=='__main__':
    main()
