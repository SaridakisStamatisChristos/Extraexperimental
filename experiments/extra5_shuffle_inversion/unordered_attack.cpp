/* Exhaustive inverse-state recovery of xorshift32 from UNORDERED 5-of-35 sets.
 * Uses only the fourth extraction index's exact 5 low bits, enumerates
 * all consistent possibilities, solves GF(2) for the hidden 32bit state,
 * then verifies all five numbers independently. Fixed 5-output sampler
 * with optional fixed inter-ticket gap. Not valid under variable skips.
 */
#include <array>
#include <algorithm>
#include <cstdint>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>
using namespace std;
struct Ticket {uint64_t mask;uint32_t allowed;};
struct Matrix{
    uint32_t pivot[32]{};uint8_t rhs[32]{};uint8_t rank=0;
    bool add(uint32_t x,uint8_t val){
        while(x){int k=31-__builtin_clz(x);
            if(pivot[k]){x^=pivot[k];val^=rhs[k];}
            else{pivot[k]=x;rhs[k]=val;rank++;return true;}
        }
        return !val;
    }
    uint32_t solve(uint32_t selected_free_bits=0)const{
        uint32_t s=selected_free_bits;
        for(int k=0;k<32;k++)if(pivot[k]){
            uint32_t lower=pivot[k]& ~(1u<<k);
            auto v=rhs[k]^(__builtin_parity(lower&s));
            s|=uint32_t(v)<<k;
        }
        return s;
    }
};
struct XorShift{int a,b,c;uint32_t multiplier=1;uint32_t step(uint32_t& s)const{
    s^=s<<a;s^=s>>b;s^=s<<c;return s;
}};
vector<Ticket> load(const string& path){
    ifstream f(path);if(!f)throw runtime_error("Cannot read input");
    string line;getline(f,line);vector<Ticket> items;
    while(getline(f,line)){
        if(line.empty())continue;
        stringstream ss(line);string part;vector<string> z;
        while(getline(ss,part,','))z.push_back(part);
        if(z.size()!=3)throw runtime_error("Bad CSV");
        Ticket t{stoull(z[1]),static_cast<uint32_t>(stoul(z[2]))};
        if(__builtin_popcountll(t.mask)!=5||!t.allowed)throw runtime_error("Invalid ticket");
        items.push_back(t);
    }
    return items;
}
uint64_t ticket(uint32_t& state,const XorShift& g,int stride){
    uint64_t mask=0;
    int remaining[35];for(int i=0;i<35;i++)remaining[i]=i+1;
    for(int k=0;k<stride;k++){
        uint32_t out=g.step(state)*g.multiplier;
        if(k<5){int n=35-k;int r=out%static_cast<uint32_t>(n);
            int v=remaining[r];mask|=1ULL<<(v-1);
            for(int i=r;i<n-1;i++)remaining[i]=remaining[i+1];
        }
    }
    return mask;
}
struct Attack {
    vector<Ticket> records;
    vector<array<uint32_t,5>> masks;
    XorShift g;
    int stride,n;
    uint64_t branches=0,leaves=0,full_states=0,verified_1=0,verified_2=0,verified_all=0;uint64_t candidate_budget=4000000;uint8_t max_free_bits=0;
    vector<uint32_t> found;
    bool budget_exceeded=false;uint64_t max_nodes=3000000;
    Attack(vector<Ticket> r, XorShift gen,int st,int num):records(move(r)),g(gen),stride(st),n(num){
        // Undo the odd output multiplier for the fourth modulo-32 constraint.
        // This does not alter the full-ticket sampler, which uses full 32-bit outputs.
        if(!(g.multiplier&1))throw runtime_error("Only odd invertible multipliers supported");
        int inverse=1;
        while(((uint32_t(inverse)*g.multiplier)&31u)!=1u)inverse+=2;
        for(auto& rec:records){
            uint32_t mask=0,v=rec.allowed;
            while(v){unsigned k=__builtin_ctz(v);v&=v-1;mask|=1u<<((k*unsigned(inverse))&31u);}
            rec.allowed=mask;
        }
        if(n>static_cast<int>(records.size())||n<8)throw runtime_error("Bad prefix");
        masks.resize(n);
        for(int bit=0;bit<32;bit++){
            uint32_t state=1u<<bit;
            for(int t=0;t<n;t++){
                for(int z=0;z<stride;z++){
                    auto value=g.step(state);
                    if(z==3){for(int b=0;b<5;b++)if(value&(1u<<b))masks[t][b]|=(1u<<bit);}
                }
            }
        }
    }
    void verify(uint32_t state){
        full_states++;
        if(!state)return;
        uint32_t s=state;
        for(int t=0;t<(int)records.size();t++){
            if(ticket(s,g,stride)!=records[t].mask)return;
            if(t==0)verified_1++;
            if(t==1)verified_2++;
        }
        verified_all++;
        found.push_back(state);
    }
    void recurse(int depth,const Matrix& mat){
        if(branches>=max_nodes){budget_exceeded=true;return;}
        branches++;
        if(mat.rank==32){verify(mat.solve());return;}
        if(depth>=n){
            leaves++;
            const int free_count=32-int(mat.rank);
            if(free_count>max_free_bits)max_free_bits=free_count;
            if(free_count>20 || (uint64_t(1)<<free_count)>candidate_budget-full_states){budget_exceeded=true;return;}
            uint32_t free_positions[32];int nfree=0;
            for(int bit=0;bit<32;bit++)if(!mat.pivot[bit])free_positions[nfree++]=1u<<bit;
            uint64_t total=uint64_t(1)<<nfree;
            for(uint64_t i=0;i<total;i++){
                uint32_t selected=0;
                for(int j=0;j<nfree;j++)if((i>>j)&1)selected|=free_positions[j];
                verify(mat.solve(selected));
            }
            return;
        }
        uint32_t v=records[depth].allowed;
        while(v){int target=__builtin_ctz(v);v&=v-1;
            Matrix child=mat;
            bool ok=true;
            for(int k=0;k<5;k++)if(!child.add(masks[depth][k],(target>>k)&1)){ok=false;break;}
            if(ok)recurse(depth+1,child);
        }
    }
    void run(){Matrix m;recurse(0,m);}
};
int main(int argc,char**argv){
    if(argc!=8 && argc!=9){cerr<<"usage: unordered_attack FILE a b c stride prefix max_tickets [odd_multiplier]\n";return 2;}
    try{
        auto rows=load(argv[1]);
        int limit=atoi(argv[7]);if(limit>0&&limit<(int)rows.size())rows.resize(limit);
        XorShift g{atoi(argv[2]),atoi(argv[3]),atoi(argv[4]), argc==9?static_cast<uint32_t>(stoull(argv[8],nullptr,0)):1u};
        if(g.a<1||g.a>31||g.b<1||g.b>31||g.c<1||g.c>31)throw runtime_error("shifts outside 1..31");
        int stride=atoi(argv[5]),n=atoi(argv[6]);
        if(stride<5||stride>50)throw runtime_error("stride outside 5..50");
        Attack a(rows,g,stride,n);a.run();
        cout<<"{\"family\":\"xorshift32_"<<g.a<<"_"<<g.b<<"_"<<g.c<<"\",\"stride\":"<<stride
        <<",\"prefix\":"<<n<<",\"multiplier\":"<<g.multiplier<<",\"tickets_checked\":"<<rows.size()<<",\"branches\":"<<a.branches
        <<",\"states_full_rank\":"<<a.full_states<<",\"underconstrained_leaves\":"<<a.leaves<<",\"max_free_bits_at_leaf\":"<<int(a.max_free_bits)
        <<",\"states_matching_first_ticket\":"<<a.verified_1<<",\"states_matching_first_two\":"<<a.verified_2
        <<",\"states_matching_all_tickets\":"<<a.verified_all<<",\"exhaustive\":"<<(!a.budget_exceeded?"true":"false")<<",\"recovered_states\":[";
        for(size_t i=0;i<a.found.size();i++){if(i)cout<<',';cout<<a.found[i];}
        cout<<"]}"<<endl;
    }catch(const exception&e){cerr<<"Error: "<<e.what()<<endl;return 1;}
}
