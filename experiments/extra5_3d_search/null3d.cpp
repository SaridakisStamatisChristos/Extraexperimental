// Whole-library null: shuffle observed training permutation labels, preserve X and T features,
// and rerun the identical 10,368,000-configuration affine search on each shuffled history.
#include <array>
#include <algorithm>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <random>
#include <sstream>
#include <string>
#include <vector>
using namespace std;
static constexpr int Q=120;
int m(int n){int r=n%Q;return r<0?r+Q:r;}
vector<string> split(string s){stringstream f(s);string v;vector<string>r;while(getline(f,v,','))r.push_back(v);return r;}
int main(int argc,char**argv){
 try{
  if(argc!=5)throw runtime_error("usage: null3d TRAIN.csv REPS SEED OUTPUT.csv");
  ifstream f(argv[1]);if(!f)throw runtime_error("missing train csv");
  string line;getline(f,line);auto hdr=split(line);auto idx=[&](string s){auto it=find(hdr.begin(),hdr.end(),s);if(it==hdr.end())throw runtime_error("missing field "+s);return int(it-hdr.begin());};
  int iids=idx("draw_id"),iday=idx("date_ordinal"),iS=idx("set_rank"),ips=idx("prev_set_rank"),ipp=idx("prev_perm_rank"),ip=idx("perm_rank");
  vector<array<int,3>>x;vector<array<int,2>>t;vector<int>y;
  while(getline(f,line)){auto r=split(line);if(r.size()!=hdr.size())throw runtime_error("malformed line");x.push_back({m(stoi(r[iS])),m(stoi(r[ips])),m(stoi(r[ipp]))});t.push_back({m(stoi(r[iids])),m(stoi(r[iday]))});y.push_back(m(stoi(r[ip])));}
  if(x.size()!=2192)throw runtime_error("wrong n");
  const int N=int(x.size());int reps=stoi(argv[2]);mt19937_64 rng(stoull(argv[3]));
  // Keep the observed permutation frequency table; null is independence from combinations and dates.
  ofstream out(argv[4]);out<<"rep,max_train_matches\n";
  array<array<vector<uint8_t>,Q>,3> ax;
  array<array<vector<uint8_t>,Q>,2> bt;
  for(int xx=0;xx<3;xx++)for(int a=0;a<Q;a++){ax[xx][a].resize(N);for(int i=0;i<N;i++)ax[xx][a][i]=uint8_t(a*x[i][xx]%Q);}
  for(int tt=0;tt<2;tt++)for(int b=0;b<Q;b++){bt[tt][b].resize(N);for(int i=0;i<N;i++)bt[tt][b][i]=uint8_t(b*t[i][tt]%Q);}
  for(int rep=0;rep<reps;rep++){
   shuffle(y.begin(),y.end(),rng);
   int maximum=0;
   for(int xx=0;xx<3;xx++)for(int tt=0;tt<2;tt++)for(int a=0;a<Q;a++){
    auto& A=ax[xx][a];
    for(int b=0;b<Q;b++){
     auto &B=bt[tt][b];int counts[Q]={};
     for(int i=0;i<N;i++){
      int c=y[i]-int(A[i])-int(B[i]);
      if(c<0)c+=Q;
      if(c<0)c+=Q;
      if(c<0||c>=Q)throw runtime_error("bad mod");
      int v=++counts[c];if(v>maximum)maximum=v;
     }
    }
   }
   out<<rep<<','<<maximum<<'\n';out.flush();
   if((rep+1)%20==0)cerr<<"null replicate "<<(rep+1)<<"/"<<reps<<" max "<<maximum<<"\n";
  }
 }catch(exception const&e){cerr<<"ERROR "<<e.what()<<'\n';return 2;}
}
