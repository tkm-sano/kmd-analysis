#include <dlfcn.h>
#include <stdlib.h>
__attribute__((constructor)) static void local_registry(void) {
 const char *p=getenv("THESIS_LANGTAG_DATADIR");
 if (!p) return;
 void *h=dlopen("liblangtag.so.1",RTLD_LAZY|RTLD_GLOBAL);
 if (h) { void (*f)(const char*)=dlsym(h,"lt_db_set_datadir"); if(f) f(p); }
}
