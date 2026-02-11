-- 캘리포니아 Community Colleges 추가
-- 빠진 학교들만 추가 (이미 있는 학교는 제외)

INSERT INTO schools (id, name, city, state, type, website, international_email, international_phone, created_at, updated_at)
VALUES
-- California Schools
(gen_random_uuid(), 'American River College', 'Sacramento', 'CA', 'community_college', 'https://arc.losrios.edu', NULL, NULL, NOW(), NOW()),
(gen_random_uuid(), 'Cerritos College', 'Norwalk', 'CA', 'community_college', 'https://www.cerritos.edu', 'international@cerritos.edu', '+1-562-860-2451', NOW(), NOW()),
(gen_random_uuid(), 'College of San Mateo', 'San Mateo', 'CA', 'community_college', 'https://collegeofsanmateo.edu', NULL, NULL, NOW(), NOW()),
(gen_random_uuid(), 'Saddleback College', 'Mission Viejo', 'CA', 'community_college', 'https://www.saddleback.edu', NULL, NULL, NOW(), NOW()),
(gen_random_uuid(), 'Santa Ana College', 'Santa Ana', 'CA', 'community_college', 'https://www.sac.edu', NULL, NULL, NOW(), NOW()),
(gen_random_uuid(), 'Chaffey College', 'Rancho Cucamonga', 'CA', 'community_college', 'https://www.chaffey.edu', 'international@chaffey.edu', '+1-909-652-7478', NOW(), NOW()),
(gen_random_uuid(), 'Norco College', 'Norco', 'CA', 'community_college', 'https://www.norcocollege.edu', NULL, NULL, NOW(), NOW()),
(gen_random_uuid(), 'Evergreen Valley College', 'San Jose', 'CA', 'community_college', 'https://www.evc.edu', 'international@evc.edu', '+1-408-274-7900', NOW(), NOW()),
(gen_random_uuid(), 'West Hills College-Lemoore', 'Lemoore', 'CA', 'community_college', 'https://www.westhillscollege.com', NULL, NULL, NOW(), NOW()),
(gen_random_uuid(), 'San Jose City College', 'San Jose', 'CA', 'community_college', 'https://www.sjcc.edu', 'international@sjcc.edu', '+1-408-298-2181', NOW(), NOW()),
(gen_random_uuid(), 'Mission College', 'Santa Clara', 'CA', 'community_college', 'https://www.missioncollege.edu', 'international@missioncollege.edu', '+1-408-855-5246', NOW(), NOW()),
(gen_random_uuid(), 'Contra Costa College', 'San Pablo', 'CA', 'community_college', 'https://www.contracosta.edu', 'international@contracosta.edu', '+1-510-235-7800', NOW(), NOW()),
(gen_random_uuid(), 'Fresno City College', 'Fresno', 'CA', 'community_college', 'https://www.fresnocitycollege.edu', 'international@fresnocitycollege.edu', '+1-559-442-4600', NOW(), NOW()),
(gen_random_uuid(), 'Allan Hancock College', 'Santa Maria', 'CA', 'community_college', 'https://www.hancockcollege.edu', NULL, NULL, NOW(), NOW()),
(gen_random_uuid(), 'Antelope Valley College', 'Lancaster', 'CA', 'community_college', 'https://www.avc.edu', NULL, NULL, NOW(), NOW()),
(gen_random_uuid(), 'Cuyamaca College', 'El Cajon', 'CA', 'community_college', 'https://www.cuyamaca.edu', NULL, NULL, NOW(), NOW()),
(gen_random_uuid(), 'San Bernardino Valley College', 'San Bernardino', 'CA', 'community_college', 'https://www.valleycollege.edu', 'international@valleycollege.edu', '+1-909-384-4400', NOW(), NOW()),
(gen_random_uuid(), 'Cypress College', 'Cypress', 'CA', 'community_college', 'https://www.cypresscollege.edu', 'international@cypresscollege.edu', '+1-714-484-7000', NOW(), NOW()),
(gen_random_uuid(), 'Palomar College', 'San Marcos', 'CA', 'community_college', 'https://www.palomar.edu', 'international@palomar.edu', '+1-760-744-1150', NOW(), NOW()),
(gen_random_uuid(), 'Ventura College', 'Ventura', 'CA', 'community_college', 'https://www.venturacollege.edu', 'international@venturacollege.edu', '+1-805-289-6000', NOW(), NOW()),
(gen_random_uuid(), 'Glendale Community College', 'Glendale', 'CA', 'community_college', 'https://www.glendale.edu', 'iso@glendale.edu', '+1-818-240-1000', NOW(), NOW()),
(gen_random_uuid(), 'MiraCosta College', 'Oceanside', 'CA', 'community_college', 'https://www.miracosta.edu', 'international@miracosta.edu', '+1-760-757-2121', NOW(), NOW()),
(gen_random_uuid(), 'Long Beach City College', 'Long Beach', 'CA', 'community_college', 'https://www.lbcc.edu', 'iso@lbcc.edu', '+1-562-938-4742', NOW(), NOW()),
(gen_random_uuid(), 'Golden West College', 'Huntington Beach', 'CA', 'community_college', 'https://www.goldenwestcollege.edu', 'international@gwc.cccd.edu', '+1-714-895-8156', NOW(), NOW()),
(gen_random_uuid(), 'Foothill College', 'Los Altos Hills', 'CA', 'community_college', 'https://www.foothill.edu', 'international@foothill.edu', '+1-650-949-7241', NOW(), NOW()),
(gen_random_uuid(), 'Ohlone College', 'Fremont', 'CA', 'community_college', 'https://www.ohlone.edu', 'international@ohlone.edu', '+1-510-659-6000', NOW(), NOW()),
(gen_random_uuid(), 'Diablo Valley College', 'Pleasant Hill', 'CA', 'community_college', 'https://www.dvc.edu', 'iso@dvc.edu', '+1-925-685-1230', NOW(), NOW()),
(gen_random_uuid(), 'Victor Valley College', 'Victorville', 'CA', 'community_college', 'https://www.vvc.edu', 'international@vvc.edu', '+1-760-245-4271', NOW(), NOW()),
(gen_random_uuid(), 'Monterey Peninsula College', 'Monterey', 'CA', 'community_college', 'https://www.mpc.edu', 'international@mpc.edu', '+1-831-646-4000', NOW(), NOW()),
(gen_random_uuid(), 'Berkeley City College', 'Berkeley', 'CA', 'community_college', 'https://www.berkeleycitycollege.edu', NULL, NULL, NOW(), NOW()),
(gen_random_uuid(), 'Butte College', 'Oroville', 'CA', 'community_college', 'https://www.butte.edu', NULL, NULL, NOW(), NOW()),
(gen_random_uuid(), 'Cabrillo College', 'Aptos', 'CA', 'community_college', 'https://www.cabrillo.edu', NULL, NULL, NOW(), NOW()),
(gen_random_uuid(), 'Barstow Community College', 'Barstow', 'CA', 'community_college', 'https://www.barstow.edu', NULL, NULL, NOW(), NOW()),
(gen_random_uuid(), 'Lake Tahoe Community College', 'South Lake Tahoe', 'CA', 'community_college', 'https://www.ltcc.edu', NULL, NULL, NOW(), NOW()),
(gen_random_uuid(), 'Los Angeles City College', 'Los Angeles', 'CA', 'community_college', 'https://www.lacitycollege.edu', NULL, NULL, NOW(), NOW()),
(gen_random_uuid(), 'Los Angeles Harbor College', 'Wilmington', 'CA', 'community_college', 'https://www.lahc.edu', NULL, NULL, NOW(), NOW()),
(gen_random_uuid(), 'Mt. San Jacinto College', 'Menifee', 'CA', 'community_college', 'https://www.msjc.edu', NULL, NULL, NOW(), NOW()),
(gen_random_uuid(), 'City College of San Francisco', 'San Francisco', 'CA', 'community_college', 'https://www.ccsf.edu', NULL, NULL, NOW(), NOW())

ON CONFLICT (name, state) DO NOTHING;

-- Texas Schools
INSERT INTO schools (id, name, city, state, type, website, international_email, international_phone, created_at, updated_at)
VALUES
(gen_random_uuid(), 'Blinn College', 'Bryan', 'TX', 'community_college', 'https://www.blinn.edu', 'international@blinn.edu', '+1-979-830-4150', NOW(), NOW()),
(gen_random_uuid(), 'Del Mar College', 'Corpus Christi', 'TX', 'community_college', 'https://www.delmar.edu', 'international@delmar.edu', '+1-361-698-1200', NOW(), NOW()),
(gen_random_uuid(), 'South Texas College', 'McAllen', 'TX', 'community_college', 'https://www.southtexascollege.edu', 'international@southtexascollege.edu', '+1-956-872-2110', NOW(), NOW()),
(gen_random_uuid(), 'Amarillo College', 'Amarillo', 'TX', 'community_college', 'https://www.actx.edu', 'international@actx.edu', '+1-806-371-5000', NOW(), NOW()),
(gen_random_uuid(), 'Lee College', 'Baytown', 'TX', 'community_college', 'https://www.lee.edu', 'international@lee.edu', '+1-281-425-6311', NOW(), NOW()),
(gen_random_uuid(), 'Galveston College', 'Galveston', 'TX', 'community_college', 'https://www.gc.edu', 'international@gc.edu', '+1-409-944-1215', NOW(), NOW()),
(gen_random_uuid(), 'Weatherford College', 'Weatherford', 'TX', 'community_college', 'https://www.wc.edu', 'international@wc.edu', '+1-817-598-6200', NOW(), NOW()),
(gen_random_uuid(), 'Paris Junior College', 'Paris', 'TX', 'community_college', 'https://www.parisjc.edu', 'international@parisjc.edu', '+1-903-785-7661', NOW(), NOW()),
(gen_random_uuid(), 'Texarkana College', 'Texarkana', 'TX', 'community_college', 'https://www.texarkanacollege.edu', NULL, NULL, NOW(), NOW()),
(gen_random_uuid(), 'Western Texas College', 'Snyder', 'TX', 'community_college', 'https://www.wtc.edu', NULL, NULL, NOW(), NOW()),
(gen_random_uuid(), 'North Central Texas College', 'Gainesville', 'TX', 'community_college', 'https://www.nctc.edu', NULL, NULL, NOW(), NOW()),
(gen_random_uuid(), 'Trinity Valley Community College', 'Athens', 'TX', 'community_college', 'https://www.tvcc.edu', NULL, NULL, NOW(), NOW()),
(gen_random_uuid(), 'Tyler Junior College', 'Tyler', 'TX', 'community_college', 'https://www.tjc.edu', 'international@tjc.edu', '+1-903-510-3301', NOW(), NOW()),
(gen_random_uuid(), 'Texas Southmost College', 'Brownsville', 'TX', 'community_college', 'https://www.tsc.edu', NULL, NULL, NOW(), NOW()),
(gen_random_uuid(), 'Cedar Valley College', 'Lancaster', 'TX', 'community_college', 'https://www.cedarvalleycollege.edu', NULL, NULL, NOW(), NOW()),
(gen_random_uuid(), 'McLennan Community College', 'Waco', 'TX', 'community_college', 'https://www.mclennan.edu', 'international@mclennan.edu', '+1-254-299-8452', NOW(), NOW()),
(gen_random_uuid(), 'Lamar State College', 'Beaumont', 'TX', 'community_college', 'https://www.lamarpa.edu', NULL, NULL, NOW(), NOW()),
(gen_random_uuid(), 'Howard College', 'Big Spring', 'TX', 'community_college', 'https://www.howardcollege.edu', NULL, NULL, NOW(), NOW()),
(gen_random_uuid(), 'Victoria College', 'Victoria', 'TX', 'community_college', 'https://www.victoriacollege.edu', NULL, NULL, NOW(), NOW()),
(gen_random_uuid(), 'Kilgore College', 'Kilgore', 'TX', 'community_college', 'https://www.kilgore.edu', NULL, NULL, NOW(), NOW()),
(gen_random_uuid(), 'Central Texas College', 'Killeen', 'TX', 'community_college', 'https://www.ctcd.edu', NULL, NULL, NOW(), NOW()),
(gen_random_uuid(), 'Alvin Community College', 'Alvin', 'TX', 'community_college', 'https://www.alvincollege.edu', NULL, NULL, NOW(), NOW()),
(gen_random_uuid(), 'Hill College', 'Hillsboro', 'TX', 'community_college', 'https://www.hillcollege.edu', NULL, NULL, NOW(), NOW()),
(gen_random_uuid(), 'Coastal Bend College', 'Beeville', 'TX', 'community_college', 'https://www.coastalbend.edu', NULL, NULL, NOW(), NOW())

ON CONFLICT (name, state) DO NOTHING;
