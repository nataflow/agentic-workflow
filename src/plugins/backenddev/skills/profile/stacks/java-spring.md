# Stack adapter — `java-spring`

Java/Kotlin di atas Spring Boot. Ditulis mengikuti `_CONTRACT.md`; tujuh seksi, urutan tetap.

## Detection

Manifest: `pom.xml` (Maven) atau `build.gradle` / `build.gradle.kts` / `gradle/libs.versions.toml` (Gradle),
di root atau satu tingkat submodule.

- **Penanda wajib**: `org.springframework.boot` atau `spring-boot` di berkas build. Repo Java tanpa
  penanda ini bukan stack `java-spring`.
- **Pemutus Maven vs Gradle**: bila keduanya hadir, build tool aktif adalah yang wrappernya
  (`./mvnw` / `./gradlew`) executable. Sebut keduanya di `## Stack` profil.
- **Nama project**: `<artifactId>` pada `pom.xml` root, atau `rootProject.name` pada `settings.gradle(.kts)`.
- **Versi framework**: `<parent><version>` dari `spring-boot-starter-parent`, atau versi plugin
  `id 'org.springframework.boot'`.
- **Versi bahasa**: `<java.version>` / `<maven.compiler.release>`, atau `sourceCompatibility` / `toolchain`.
- **Entrypoint**: kelas beranotasi `@SpringBootApplication` —
  `find . -path ./target -prune -o -name "*Application.java" -print`. Package kelas itu = `root_namespace`;
  direktorinya = `source_root` (lazim `src/main/java/<...>`).

Dependensi penanda per kelompok:

| Kelompok | Paket |
|---|---|
| DB & migration | `postgresql`, `mysql-connector-j`, `ojdbc*`, `flyway-core`, `liquibase-core`, `spring-boot-starter-data-jpa` |
| Messaging | `spring-boot-starter-amqp`, `spring-kafka`, `amazon-sqs-java-messaging-lib` |
| Cache | `spring-boot-starter-data-redis`, `caffeine`, `ehcache` |
| Security & web | `spring-boot-starter-security`, `-web`, `-webflux`, `-websocket` |
| Codegen | `lombok`, `mapstruct`, `modelmapper` |
| Batch & scheduling | `spring-boot-starter-batch`, `-quartz` |

Konfigurasi per environment: `src/main/resources/application.yml|properties` dan `application-*.yml`.
Setelan yang mengubah semantik runtime: `spring.jpa.hibernate.ddl-auto`, `spring.jpa.open-in-view`,
`spring.main.allow-circular-references`, `spring.datasource.hikari.maximum-pool-size`.

Penanda zona waktu runtime: `TimeZone.setDefault` di kelas `@SpringBootApplication` atau method
`@PostConstruct`; `spring.jackson.time-zone` di tiap `application*.yml`;
`System.setProperty("user.timezone", ...)`; `-Duser.timezone` di berkas build, `Dockerfile`, atau skrip startup.

## Commands

| Perintah | Maven | Gradle |
|---|---|---|
| build | `./mvnw clean compile` | `./gradlew build -x test` |
| typecheck | tidak berlaku (kompilasi = `build`) | tidak berlaku (kompilasi = `build`) |
| typecheck-scoped | `./mvnw -pl <module> -am compile` (tanpa `clean`) | `./gradlew :<module>:compileJava` |
| typecheck-per-brief | `tidak` — kompilasi = build penuh; biayanya tidak sepadan per brief | `tidak` — idem |
| lint | `./mvnw checkstyle:check` bila plugin terpasang | `./gradlew check -x test` |
| test | `./mvnw test` | `./gradlew test` |
| test-single | `./mvnw test -Dtest=<Class>#<method>` | `./gradlew test --tests <Class>.<method>` |
| migration | Flyway `./mvnw flyway:migrate`; Liquibase `./mvnw liquibase:update` | tugas Gradle padanannya |

Migrasi: Flyway di `src/main/resources/db/migration/` pola `V{n}__{deskripsi}.sql`; Liquibase di
`src/main/resources/db/changelog/` dengan master `db.changelog-master.yaml|xml`. High-water mark =
`{n}` tertinggi yang benar-benar ada.

## Layer taxonomy

Urutan eksekusi kode dalam satu brief: **Entity & Migration → Repository → Service → DTO & Controller → Test**.

| Layer | Penamaan | Letak lazim |
|---|---|---|
| Entity | `<Nama>.java` beranotasi `@Entity` | `entity/`, `model/`, atau root module |
| Repository | `<Nama>Repository.java` | `repository/` |
| Query dinamis | `<Nama>Specification.java` | `specification/` atau `repository/` |
| Service | `<Nama>Service.java` (+ `Impl` bila memakai interface) | `service/` |
| Controller | `<Nama>Controller.java` | `controller/` |
| DTO | request/response terpisah | `dto/request/`, `dto/response/` |

Lima jebakan yang wajib dijaga saat menulis kode di layer ini:

1. **Migrasi**: skema baru selalu lewat berkas migrasi baru; dilarang keras mengedit migrasi lama.
   Nomor versi diambil dari nomor tertinggi yang **benar-benar ada**. Kolom `NOT NULL` baru di tabel
   berisi data wajib `DEFAULT` atau backfill.
2. **Fetch plan**: `@ManyToOne`/`@OneToOne` wajib `LAZY`; relasi yang dibaca dalam loop wajib
   `JOIN FETCH` atau `@EntityGraph`.
3. **Transaksi**: `@Transactional(readOnly = true)` HANYA di method baca — di method tulis ia
   mematikan dirty-checking Hibernate.
4. **Proxy AOP**: `@Transactional`, `@Async`, `@Cacheable` mati di method `private`/`final` dan saat
   dipanggil `this.method()` dari kelas yang sama; `REQUIRES_NEW` didelegasikan ke bean terpisah.
5. **Mirrored paths**: sesuaikan `@RabbitListener`/`@KafkaListener`/`@Scheduled` bila terdaftar di
   `## Invariants` profil.

Berkas build (`pom.xml`, `build.gradle`) tidak boleh dimutasi oleh brief implementasi.

## Navigation recipes

| Target | Resep lokalisasi |
|---|---|
| Deklarasi kelas/interface/enum | `Glob` `**/<Nama>.java`; bila >1, `Grep -n "class\|interface\|enum <Nama>"` |
| Pemakai simbol | `Grep -n "<Simbol>"` di `source_root`, saring `import ...;` |
| Pemanggil method | `Grep -n "\.<method>\("`, telusuri receiver via `Read` |
| Implementasi / subclass | `Grep -n "implements <Interface>\|extends <Base>"` |
| Rantai Controller→Service→Repository | `Glob` `**/*Controller.java` → `Grep -n @GetMapping/@PostMapping` → `Read` handler, catat field service → `Glob` `**/<Service>.java` → `Read` method → `Glob` `**/<Repository>.java`; cek `@Transactional(readOnly)` |
| Akses penyimpanan | `Grep -n "JpaRepository\|CrudRepository\|@Query\|EntityManager"` |
| Aturan bisnis enum | `Grep -n "<Enum>"` (saring import) → `Read` ber-offset pada `if`/`switch` enum |
| Messaging / Scheduler | `"@RabbitListener\|@KafkaListener\|RabbitTemplate\|KafkaTemplate"` / `"@Scheduled\|JobDetail\|CronTrigger"` (periksa flag guard) |
| WebSocket / Security | `"@MessageMapping\|SimpMessagingTemplate"` / `"SecurityFilterChain\|@PreAuthorize\|@Secured"` |
| Exception handling | `"@ExceptionHandler\|@RestControllerAdvice"` |
| Config & schema | `Glob` `**/application*.{yml,yaml,properties}` → `Grep -n "<key>"`; kode: `"@Value.*<key>\|@ConfigurationProperties"`; migrasi `**/db/migration/**/*.sql` atau `**/db/changelog/**` |
| Event & observability | `"ApplicationEventPublisher\|@EventListener\|@TransactionalEventListener\|MeterRegistry\|LoggerFactory.getLogger"` |

Offset baca di sekitar baris temuan `L`: `max(1, L-15)` sampai `L+35` — cukup menangkap anotasi,
signature, dan boundary transaksi.

## Audit checklist

#### `security`

- **Endpoint tanpa proteksi otorisasi.** Tanpa `@PreAuthorize` atau pemeriksaan role/permission.
- **Bypass scoping tenant/store via parameter request.** `storeId`/`tenantId` dibaca dari body/query alih-alih konteks otentikasi.
- **SQL Injection.** Input digabung via konkatenasi string di native query alih-alih parameter binding.
- **Mass assignment.** Request body di-bind langsung ke entity JPA, memungkinkan manipulasi field privat (`role`, `balance`).
- **Logging data sensitif.** Password, token, nomor kartu, PII ter-log via logger atau `toString()`.
- **Hardcoded secret.** Kredensial di kode alih-alih vault/environment/config.
- **Path `permitAll()` terlalu longgar.** Pola `/api/**` membuka endpoint privat tanpa autentikasi.
- **Upload file tanpa validasi tipe/ukuran.** Risiko DoS atau eksekusi berkas berbahaya.
- **Error message membocorkan struktur internal.** Stack trace atau SQL mentah keluar ke response.

#### `transaction`

- **`@Transactional` pada self-invocation (`this.method()`), method `private`, atau `final`.** Melewati proxy Spring AOP sehingga atribut (`REQUIRES_NEW`, `readOnly`, `timeout`, `rollbackFor`) diabaikan atau transaksi tidak aktif sama sekali.
- **Mutasi data di luar boundary `@Transactional`.** Tanpa transaksi aktif atau setelah transaksi caller commit (`@TransactionalEventListener(AFTER_COMMIT)`, `Propagation.NOT_SUPPORTED`). Gagal di tengah meninggalkan data parsial tanpa rollback.
- **`readOnly = true` pada method yang memutasi data.** Flush JPA tidak jalan atau runtime exception.
- **Publish message/event ke broker sebelum transaksi commit.** Consumer memproses data uncommitted; bila rollback, pesan merujuk data hantu. Gunakan outbox atau `AFTER_COMMIT`.
- **`@Transactional` di method controller.** Menahan koneksi DB sepanjang siklus HTTP request-response.
- **Commit tak sengaja akibat checked exception.** Default Spring hanya rollback pada `RuntimeException`/`Error`; checked exception tanpa `rollbackFor` tetap commit.
- **Race condition mutasi stok/kuota tanpa lock.** Baca lalu tulis tanpa `@Lock(PESSIMISTIC_WRITE)`, `SELECT ... FOR UPDATE`, atau versioning optimistic ber-retry. *(Bila akibat scheduler tumpang tindih → `concurrency`)*

#### `data`

- **`double`/`float` untuk nominal uang, kuantitas, atau persentase.** Error akumulasi pecahan desimal biner; wajib `BigDecimal` atau integer unit terkecil.
- **`BigDecimal` tanpa `scale`/`RoundingMode` eksplisit pada `divide()`.** Risiko `ArithmeticException`.
- **`BigDecimal.equals()` alih-alih `compareTo(...) == 0`.** `equals()` membandingkan scale (`0.10` != `0.1`).
- **`Optional.get()` / `findById().get()` tanpa `isPresent()`, atau unboxing nullable wrapper.**
- **`@Valid`/`@Validated` hilang pada `@RequestBody` DTO ber-constraint** (`@NotNull`, `@Size`, `@Min`).
- **Validasi hanya di controller**, tidak ditegakkan di consumer/scheduler/importer yang menulis entity sama.
- **`LocalDateTime` untuk momen lintas zona waktu.** Tidak membawa offset; wajib `Instant` / `OffsetDateTime` / `ZonedDateTime`.
- **Perbandingan tanggal mengabaikan boundary.** Filter `createdAt <= endDate` bertipe date-only.
- **Enum ditambah tanpa memperbarui `switch`/mapping** (kehilangan cabang default yang melempar error).
- **Inkonsistensi pembulatan atau konversi satuan antar-layer.**

#### `persistence`

- **N+1 query dari relasi `LAZY` di dalam loop**, termasuk `@ManyToOne`/`@OneToOne` yang dibiarkan default `EAGER`.
- **`findAll()` tanpa paging** pada tabel yang berpotensi membesar (`OutOfMemoryError`/timeout).
- **Akses relasi `LAZY` saat session ditutup (`spring.jpa.open-in-view=false`).** Memicu `LazyInitializationException` di serialisasi response.
- **`JOIN FETCH` collection bersama `Pageable`.** Hibernate melakukan pagination di memori, bukan SQL.
- **`Specification` join to-many menduplikasi baris tanpa `distinct`.** Hibernate 5 menduplikasi entity; Hibernate 6 membuat total halaman/count salah di SQL.
- **`JoinType` keliru (inner vs left) pada relasi opsional.** Membuang baris root yang relasinya `null`.
- **Query per elemen di dalam loop.** `findById` berulang alih-alih `findAllById(ids)`.
- **`@OneToMany` dengan `CascadeType.ALL` tidak disengaja.** Simpan/hapus parent menghapus seluruh anak.
- **Entity JPA dikembalikan langsung sebagai response API.** Jackson memicu traversal lazy di luar transaksi. *(Request body di-bind ke entity → `security`; batas layer service → `architecture`)*

#### `concurrency`

- **Consumer tanpa penanganan idempotent.** Retry broker memicu pemrosesan ganda.
- **Pesan tanpa dead-letter queue (DLQ) atau limit retry.**
- **Scheduler overlap tanpa lock.** Eksekusi multi-instance konkuren tanpa distributed lock.
- **Async kehilangan konteks security/transaksi.** Thread `@Async` tidak mewarisi `SecurityContextHolder`.
- **`@Async` pada self-invocation (`this.method()`).** Melewati proxy dan berjalan sinkron.
- **Publish ke queue tanpa handling kegagalan pengiriman.**
- **Panggilan keluar tanpa timeout atau batas retry.**
- **Mirrored path tidak sinkron.** Mutasi entity sinkron (HTTP) tidak selaras dengan jalur asinkron (queue/scheduler) yang terdaftar di `## Invariants` profil.
- **Perilaku keliru saat feature flag consumer/scheduler nonaktif** (`ENABLE_CONSUMER`, dsb.).

#### `architecture`

- **Logika bisnis di controller.** Percabangan aturan dan orkestrasi ditulis langsung di handler HTTP.
- **Dependensi sirkular antar-service.** Circular injection constructor gagal startup di Spring Boot ≥2.6 (kecuali `spring.main.allow-circular-references=true`); circular call mengaburkan batas transaksi.
- **Repository dipanggil langsung dari controller**, melewati layer service.
- **DTO dan Entity JPA bercampur di batas layer internal.**
- **Mapping DTO↔entity menyimpang dari pola module tetangga.**
- **Duplikasi logika yang sudah ada di module shared** (`libraries/`, `common/`, `shared/` di profil).
- **Melempar generic `Exception` alih-alih domain exception spesifik.**
- **Magic number/string alih-alih konstanta bernama atau enum.**
- **Mutable state di singleton bean.** Field non-final di `@Service`/`@RestController`, atau objek non-thread-safe (`SimpleDateFormat`).
- **Cache key mengabaikan scoping tenant/user** (`@Cacheable` tanpa scope key; `@CacheEvict` hilang; `@Cacheable` self-invocation).

## API surface

Endpoint dideklarasikan lewat anotasi kelas dan method:

- **Kelas**: `@RestController` / `@Controller`, prefix dari `@RequestMapping("/...")` pada kelas
  ditambah `server.servlet.context-path` di konfigurasi.
- **Method + path**: `@GetMapping`, `@PostMapping`, `@PutMapping`, `@PatchMapping`, `@DeleteMapping`,
  atau `@RequestMapping(method = ...)`.
- **Parameter**: `@PathVariable`, `@RequestParam` (perhatikan `required` dan `defaultValue`),
  `@RequestBody`, `@RequestHeader`.
- **Bentuk response**: tipe kembalian method; bila `ResponseEntity<T>`, `T` yang dipetakan. Bungkus
  generik repo (`ApiResponse<T>`) dicatat sekali di kepala dokumen, bukan diulang per endpoint.
- **Status code**: `@ResponseStatus` pada method, atau argumen `ResponseEntity.status(...)`; default
  `200` untuk method tanpa keduanya.
- **Otorisasi per endpoint**: `@PreAuthorize` / `@Secured` pada method atau kelas, ditambah aturan
  pola URL di `SecurityFilterChain`.
- **Validasi request**: constraint Jakarta Validation pada DTO (`@NotNull`, `@Size`, `@Min`) yang
  aktif hanya bila `@Valid` hadir di parameter handler.
- **Bentuk error**: `@RestControllerAdvice` + `@ExceptionHandler`.

## Failure signatures

Bentuk error runtime yang khas dan cara membacanya:

- **Stacktrace JVM.** Frame paling informatif adalah frame pertama yang package-nya cocok dengan
  `root_namespace`, bukan frame teratas (yang lazimnya milik framework atau driver). Rantai
  `Caused by:` dibaca dari **paling bawah** — akar sebenarnya ada di sana.
- **`LazyInitializationException`** — relasi lazy diakses di luar transaksi; lihat `open-in-view` dan
  batas `@Transactional` method pemanggil.
- **`TransactionRequiredException` / mutasi tak tersimpan tanpa error** — proxy AOP tidak aktif;
  periksa self-invocation dan modifier method.
- **`ObjectOptimisticLockingFailureException`** — dua penulis pada baris ber-`@Version` yang sama.
- **`DataIntegrityViolationException` / `ConstraintViolationException`** — bedakan keduanya:
  yang pertama dari DB, yang kedua dari Jakarta Validation.
- **`BeanCurrentlyInCreationException` / `UnsatisfiedDependencyException`** saat startup —
  dependensi sirkular atau bean yang tidak terdaftar.
- **`FlywayValidateException` saat startup** — checksum migrasi berubah, tanda migrasi lama diedit.
- **HTTP 500 tanpa stacktrace di log** — exception tertangkap `@RestControllerAdvice` yang menelannya;
  periksa handler-nya lebih dulu sebelum menduga kegagalan lain.
- **Test merah hanya saat suite penuh** — kebocoran state antar-test; periksa `@DirtiesContext`,
  data statis, dan urutan transaksi test.
